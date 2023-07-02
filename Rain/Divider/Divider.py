import os
import numpy as np
from Rain.Divider.DividerAmbassador import DividerAmbassador
from Rain.Divider.DeepLearning.DeepLearningFactory import DeepLearningFactory
from Rain.TemporaryFilesManager.TemporaryFilesManager import TemporaryFilesManager
from Rain.LogService.LogService import LogService


class Divider:
    def __init__(self, model, config):
        self.num_of_workers = config["partitions"]
        self.partitions = config["partitions"]
        self.logger = LogService("Divider")
        self.divider_ambassador = DividerAmbassador()

        # define the coord & provisioner IPs
        self.coordinator_IP = '127.0.0.1'
        self.provisioner_IP = '127.0.0.1'
        
        self.model_base_path = "../../../../Rain/Divider/divider/data/"
        if not os.path.exists(self.model_base_path):
            os.makedirs(self.model_base_path)

        # define the interface
        if config["learning_type"] == "DL":
            self.algorithm = DeepLearningFactory.create_DL_interface(model, config, self.divider_ambassador)
        elif config["learning_type"] == "ML":
            self.algorithm = None

    def serve(self):
        self.divider_ambassador.serve()

    def stop_serving(self):
        self.divider_ambassador.stop_serving()
        self.logger.log('debug', f"Divider stopped serving")


    def send_data_to_workers(self, X_train, y_train):
        try: 
            X_train_partitions, y_train_partitions = self.partition_train_data(X_train, y_train)
            self.logger.log('debug', f"Data partitioned")
        except Exception as e:
            self.logger.log('debug', f"Error in partitioning data: {e}")
            return
        try:
            self.divider_ambassador.send_data(self.coordinator_IP, self.num_of_workers, X_train_partitions, y_train_partitions)
        except Exception as e:
            self.logger.log('debug', f"Error in sending data to workers: {e}")
            return


    def partition_train_data(self, X_train, y_train):
        num_samples = X_train.shape[0]

        # Create an array of indices from 0 to num_samples - 1
        indices = np.arange(num_samples)

        # Shuffle the indices
        np.random.shuffle(indices)

        # Use the shuffled indices to shuffle the datasets
        X_train = X_train[indices]
        y_train = y_train[indices]

        X_train_partitions = []
        y_train_partitions = []

        partition_size = int(len(X_train) / self.partitions)

        for i in range(self.partitions):
            if i == self.partitions - 1:
                X_train_partitions.append(X_train[i * partition_size :])
                y_train_partitions.append(y_train[i * partition_size :])
            else:
                X_train_partitions.append(X_train[i * partition_size : (i + 1) * partition_size])
                y_train_partitions.append(y_train[i * partition_size : (i + 1) * partition_size])

        return X_train_partitions, y_train_partitions

    def send_info_to_workers(self, iteration_num):
        self.algorithm.send_info_to_workers(iteration_num)

    
    def train_centralized_sync(self):
        model = self.algorithm.train_centralized_sync()
        return model

    def train_centralized_async(self):
        model = self.algorithm.train_centralized_async()
        return model


    # destructor 
    def __del__(self):
        self.divider_ambassador.stop_serving()