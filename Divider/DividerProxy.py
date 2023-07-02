from Divider.Divider import Divider
import sys
import numpy as np
sys.path.append('../LogService')
from LogService.LogService import LogService
sys.path.pop()

class DividerProxy():
    def __init__(self, config, model):
        self.divider = Divider(model, config)
        self.logger = LogService("DividerProxy")

    def __del__(self):
        del self.divider
    
    def train(self, X_train, y_train, strategy='sync'):
        # send data
        self.divider.serve()
        self.logger.log('debug', f"Sending data to workers")
        self.divider.send_data_to_workers(X_train, y_train)
        # train
        self.logger.log('debug', f"Training")
        if strategy == 'sync':
            return self.train_centralized_sync()
        elif strategy == 'async':
            return self.train_centralized_async()
        else:
            raise Exception("Invalid strategy")

    def train_centralized_sync(self):
        model = self.divider.train_centralized_sync()
        self.divider.stop_serving()      
        return model


    def train_centralized_async(self, X_train, y_train):
        # send data
        self.divider.serve()
        self.logger.log('debug', f"Sending data to workers")
        X_train, y_train = self.divider.partition_train_data(X_train, y_train)
        for i in range(len(X_train)):
            np.save(f"../../../data/X_train_{i + 1}.npy", X_train[i])
            np.save(f"../../../data/y_train_{i + 1}.npy", y_train[i])
        self.divider.send_data_to_workers()
        # train
        self.logger.log('debug', f"Training")
        model = self.divider.train_centralized_async() 
        self.divider.stop_serving()     
        return model