import os
import numpy as np
import dill
from Rain.Divider.DividerAmbassador import DividerAmbassador
from Rain.Divider.DeepLearning.DeepLearningFactory import DeepLearningFactory
from Rain.TemporaryFilesManager.TemporaryFilesManager import TemporaryFilesManager
from Rain.LogService.LogService import LogService


class Divider:
    def __init__(self):
        self.num_of_workers = None
        self.partitions = None
        self.logger = LogService("Divider")
        self.divider_ambassador = DividerAmbassador()        
        self.model_base_path = TemporaryFilesManager.get_instance().create_temp_dir('divider/')
        self.algorithm = None

    def __del__(self):
        self.divider_ambassador.stop_serving()

    def serve(self):
        self.divider_ambassador.serve()

    def stop_serving(self):
        self.divider_ambassador.stop_serving()
        self.logger.log('debug', f"Divider stopped serving")

    def read_data(self):
        """
        Reads the data from the temporary files
        Read the model and the config from the temporary files
        return: X, y, model, config
        """
        try:
            X = np.load(self.model_base_path + 'x_train.npy')
            y = np.load(self.model_base_path + 'y_train.npy')
            self.model = dill.load(open(f"{self.model_base_path}initial_model.pkl", "rb"))
            self.config = dill.load(open(f"{self.model_base_path}config.pkl", "rb"))
            self.logger.log('debug', self.config)

            self.partitions = self.config["partitions"]
            self.num_of_workers = self.config["partitions"]

            # # define the interface
            if self.config["learning_type"] == "DL":
                self.algorithm = DeepLearningFactory.create_DL_interface(self.model, self.config, self.divider_ambassador)
            elif self.config["learning_type"] == "ML":
                self.algorithm = None
            else: 
                raise Exception("Unknown learning type")

            self.logger.log('debug', f"Data read in divider successfully")
            return X, y
        except Exception as e:
            self.logger.log('debug', f"Error in reading data in divider: {e}")
            return


    def __partition_data(self, X, y):
        num_samples = X.shape[0]

        # to make the data independent and identically distributed (i.i.d.) subsets
        indices = np.random.permutation(num_samples) 

        # Use the shuffled indices to shuffle the datasets
        X = X[indices]
        y = y[indices]

        X_train_partitions = []
        y_train_partitions = []

        partition_size = int(len(X) / self.partitions)

        for i in range(self.partitions):
            if i == self.partitions - 1:
                X_train_partitions.append(X[i * partition_size :])
                y_train_partitions.append(y[i * partition_size :])
            else:
                X_train_partitions.append(X[i * partition_size : (i + 1) * partition_size])
                y_train_partitions.append(y[i * partition_size : (i + 1) * partition_size])

        return X_train_partitions, y_train_partitions
    
    def send_data_to_workers(self, X, y):
        try: 
            X_partitions, y_partitions = self.__partition_data(X, y)
            self.logger.log('debug', f"Data partitioned")
        except Exception as e:
            self.logger.log('debug', f"Error in partitioning data: {e}")
            return
        try:
            self.divider_ambassador.send_data(self.num_of_workers, X_partitions, y_partitions)
        except Exception as e:
            self.logger.log('debug', f"Error in sending data to workers: {e}")
            return

    def send_info_to_workers(self, iteration_num):
        self.algorithm.send_info_to_workers(iteration_num)

    def save_model(self, model):
        try:
            dill.dump(model, open(f"{self.model_base_path}model.pkl", "wb"))
            self.logger.log('debug', f"Model saved in divider")
        except Exception as e:
            self.logger.log('debug', f"Error in saving model in divider: {e}")
            return


    def send_model_to_proxy(self):
        try:
            response = self.divider_ambassador.send_model()
            self.logger.log('debug', f"Model sent to divider proxy")
        except Exception as e:
            self.logger.log('debug', f"Error in sending model to divider proxy: {e}")
            return

    def train(self, strategy):

        # send data to workers
        self.logger.log('debug', f"Sending data to workers")
        X,y = self.read_data()

        self.send_data_to_workers(X, y)

        if strategy == 'sync':
            model = self.algorithm.train_centralized_sync()
        elif strategy == 'async':
            model = self.algorithm.train_centralized_async() 
        else:
            raise Exception("Invalid strategy")

        # save the model
        self.logger.log('debug', f"divider is saving the model")
        self.save_model(model)

        # send the model to the divider proxy
        self.logger.log('debug', f"Sending the model to the divider proxy")
        self.send_model_to_proxy()

        self.stop_serving()     
        return 


