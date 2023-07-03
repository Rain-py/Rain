from Rain.Divider.Divider import Divider
from Rain.LogService.LogService import LogService

class DividerProxy():
    def __init__(self, config, model):
        self.divider = Divider(model, config)
        self.logger = LogService("DividerProxy")

    def __del__(self):
        del self.divider
    
    def train(self, X_train, y_train, strategy='sync'):
        try:
            # send data
            self.divider.serve()
            self.logger.log('debug', f"Sending data to workers")
            self.divider.send_data_to_workers(X_train, y_train)
            # train
            self.logger.log('debug', f"Training Started")
            model = self.divider.train(strategy)
            self.divider.stop_serving()
            return model 
        except Exception as e:
            self.logger.log('error', f"Error in training: {e}")
            return None

