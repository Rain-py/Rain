from Divider.Divider import Divider
import sys
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
        self.logger.log('debug', f"Training Started")
        if strategy == 'sync':
            model = self.divider.train_centralized_sync()
            self.divider.stop_serving()      
            return model 
        elif strategy == 'async':
            model = self.divider.train_centralized_async() 
            self.divider.stop_serving()     
            return model 
        else:
            raise Exception("Invalid strategy")
