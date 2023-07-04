from Rain.Divider.Divider import Divider
from Rain.LogService.LogService import LogService

class DividerProxy():
    def __init__(self, config, model):
        self.divider = Divider(model, config)
        self.logger = LogService("DividerProxy")

    def __del__(self):
        try:
            del self.divider
        except Exception as e:
            self.logger.log('error', f"Error deleting: {e}")
    
    def train(self, X_train, y_train, strategy='sync'):
        try:
            # send data
            self.divider.serve()
            # train
            self.logger.log('debug', f"Training Started")
            model = self.divider.train(strategy, X_train, y_train)
            self.divider.stop_serving()
            return model 
        except Exception as e:
            self.logger.log('error', f"Error in training: {e}")
            return None

