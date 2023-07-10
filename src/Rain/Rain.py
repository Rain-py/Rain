from Rain.Provisioner.Provisioner import Provisioner
from Rain.Divider.DividerProxy import DividerProxy
from Rain.LogService.LogService import LogService
from Rain.TemporaryFilesManager.TemporaryFilesManager import TemporaryFilesManager
import numpy as np


class Rain:
    def __init__(self, config : dict, model : any = None) -> None:
      """
      Function to initialize the Rain.

      Args:
          config (dict): configuration settings.
          model (any, optional): the model to be trained (if machine learning, pass None).
      """   
      self.config = config
      # self.config_handler = ConfigHandler()
      # create a logger for the Rain file.
      self.logger = LogService("Rain")
      try:
        # validate the config.
        # self.config_handler.validate_config(config)
        pass
      except Exception as e:
        self.logger.log("error", f"Error in the config: {e}")
      # create a temporary directory for the Rain to store its data.
      self.temp_manager = TemporaryFilesManager.get_instance(config["temp_data_path"] if "temp_data_path" in config else None)
      self.logger.log('info', f"Rain is initialized")
      # create a provisioner to instantiate the workers.
      self.provisioner = Provisioner(self.config)
      # create a divider proxy to divide the data and train the model.
      self.divider_proxy = DividerProxy(config, model)

    def __del__(self) -> None:
      """
      Function to delete the Rain and all instance that are used.
      """
      try:
        self.provisioner.stop_serving()
        del self.provisioner
        del self.divider_proxy
      except Exception as e:
          self.logger.log('error', f"Error deleting: {e}")

    def train(self, X_train : np.ndarray, y_train : np.ndarray, strategy : str = 'sync') -> any:
      """
      Function to train the model.
      
      Args:
          X_train (np.ndarray): X train data
          y_train (np.ndarray): y train data (if unsupervised, pass None)
          strategy (str, optional): strategy to update the model gradients. Defaults to 'sync'.

      Returns:
          any: it returns the trained model (it may be deep or machine learning model).
      """
      try:
        self.provisioner.serve()
        model = self.divider_proxy.train(X_train, y_train, strategy)
        # TODO: take an action. 
        # self.provisioner.stop_serving()
        return model
      except Exception as e:
        self.logger.log('error', f"Error training the model: {e}")
        self.provisioner.stop_serving()
        return


    

    

    
    
