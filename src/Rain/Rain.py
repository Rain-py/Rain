

from Rain.Provisioner.Provisioner import Provisioner
from Rain.Divider.DividerProxy import DividerProxy
from Rain.LogService.LogService import LogService
from Rain.TemporaryFilesManager.TemporaryFilesManager import TemporaryFilesManager
class Rain:
    def __init__(self, config, model=None):
        self.config = config
        self.logger = LogService("Rain")
        self.temp_manager = TemporaryFilesManager.get_instance(config["temp_data_path"] if "temp_data_path" in config else None)
        self.logger.log('debug', f"Rain is initialized")
        self.provisioner = Provisioner(self.config)
        self.divider_proxy = DividerProxy(config, model)
        self.ip_addresses = []

    def __del__(self):
        try:
          del self.provisioner
          del self.divider_proxy
          del self.temp_manager
        except Exception as e:
           self.logger.log('error', f"Error deleting: {e}")

    def train(self, X_train, y_train, strategy='sync'):
        # create workers
        self.logger.log('debug', f"Creating workers")
        try:
          self.provisioner.serve()
          model = self.divider_proxy.train(X_train, y_train, strategy) 
          
          self.provisioner.stop_serving()
        except Exception as e:
          self.logger.log('error', f"Error training the model: {e}")
          self.provisioner.stop_serving()
          return

        return model
        
# Config example:
'''
config = {
  "mode": {
      "type": "local",
      "params": {
      "num_of_workers": 3,
      
      }
      
  },
  "partitions": 3,
  "iterations": 3,
  "learning_type": "DL",
  "DL": {
    "lib": {
      "type": "tensorflow",
      "params": {
        "loss": tf.keras.losses.CategoricalCrossentropy(),
        "optimizer": tf.keras.optimizers.Adam(learning_rate=0.001),

      }
    },
    "lr": 0.001,
    "epochs": 2,
    "batch_size": 128,
  },
  "ML": {
      "algorithm": {
      "type": "KNN",
      "params": {
        "K": 5,
        "metric": "euclidean"
      }
    }    
  }
}
'''

    

    

    
    
