import numpy as np
from Rain.Divider.DividerAmbassador import DividerAmbassador
from Rain.Divider.DeepLearning.DeepLearningFactory import DeepLearningFactory
from Rain.Divider.MachineLearning.MachineLearningFactory import MachineLearningFactory
from Rain.TemporaryFilesManager.TemporaryFilesManager import TemporaryFilesManager
from Rain.LogService.LogService import LogService


class Divider:
    def __init__(self, model, config):
        self.num_of_workers = config["partitions"]
        self.partitions = config["partitions"]
        self.logger = LogService("Divider")
        self.divider_ambassador = DividerAmbassador()        
        self.model_base_path = TemporaryFilesManager.get_instance().create_temp_dir('divider/')

        # define the interface
        if config["learning_type"] == "DL":
            self.algorithm = DeepLearningFactory.create_DL_interface(model, config, self.divider_ambassador)
        elif config["learning_type"] == "ML":
            self.algorithm = MachineLearningFactory.create_ML_interface(config, self.divider_ambassador)
        else: 
            raise Exception("Unknown learning type")

    def __del__(self):
        try:
            del self.divider_ambassador
        except Exception as e:
            self.logger.log('error', f"Error deleting: {e}")

    def serve(self):
        self.divider_ambassador.serve()

    def stop_serving(self):
        try:
            self.divider_ambassador.stop_serving()
            self.logger.log('debug', f"Divider stopped serving")
        except Exception as e:
            self.logger.log('error', "Error stopping serving: " + str(e))
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

    def send_info_to_workers(self, iteration_num):
        self.algorithm.send_info_to_workers(iteration_num)

    def train(self, strategy, X, y):
        if y is None:
            y = np.zeros(X.shape[0])
        # partition the data
        X_train_partitions, y_train_partitions = self.__partition_data(X, y)
        if strategy == 'sync':
            model = self.algorithm.train_centralized_sync(X_train_partitions, y_train_partitions)
        elif strategy == 'async':
            model = self.algorithm.train_centralized_async(X_train_partitions, y_train_partitions) 
        else:
            raise Exception("Invalid strategy")
        return model 


