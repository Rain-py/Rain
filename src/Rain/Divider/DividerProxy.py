from Rain.Divider.Divider import Divider
from Rain.LogService.LogService import LogService
import numpy

class DividerProxy():
    def __init__(self, config : dict, model : str) -> None:
        """
        Function to initialize the divider proxy.

        Args:
            config (dict): configuration settings.
            model (str): the model to be trained.
        """
        self.divider = Divider(config, model)
        self.logger = LogService("DividerProxy")

    def __del__(self) -> None:
        """
        Function to delete the divider proxy.
        """
        try:
            del self.divider
        except Exception as e:
            self.logger.log('error', f"Error deleting: {e}")
    
    def train(self, X_train : numpy.ndarray, y_train : numpy.ndarray, strategy : str = 'sync') -> any:
        """
        Function to train the model.
        
        Args:
            X_train (numpy.ndarray): X train data
            y_train (numpy.ndarray): y train data (if unsupervised, pass None)
            strategy (str, optional): strategy to update the model gradients. Defaults to 'sync'.

        Returns:
            model: return the trained model
        """
        try:
            self.divider.serve()
            self.logger.log('debug', f"Training Started")
            # train
            model = self.divider.train(strategy, X_train, y_train)
            self.divider.stop_serving()
            return model 
        except Exception as e:
            self.logger.log('error', f"Error in training: {e}")
            return None

