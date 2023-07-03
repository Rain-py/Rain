

from Rain.Provisioner.Provisioner import Provisioner
from Rain.Divider.DividerProxy import DividerProxy
from Rain.LogService.LogService import LogService
from Rain.TemporaryFilesManager.TemporaryFilesManager import TemporaryFilesManager
class Rain:
    def __init__(self, config, model=None):
        self.logger = LogService("Rain")
        self.temp_manager = TemporaryFilesManager.get_instance()
        self.logger.log('debug', f"Rain is initialized")
        self.config = config
        self.provisioner = Provisioner(self.config['mode'])
        self.divider_proxy = DividerProxy(config, model)
        self.ip_addresses = []

    def __del__(self):
        del self.provisioner
        del self.divider_proxy
        del self.logger
        del self.temp_manager

    def train(self, X_train, y_train, strategy='sync'):
        # create workers
        self.logger.log('debug', f"Creating workers")
        self.provisioner.serve()
        model =  self.divider_proxy.train(X_train, y_train, strategy) 
        self.provisioner.stop_serving()
        return model
        
# Config example:
'''
config = {
  "mode": "local",
  "partitions": 3,
  "num_of_workers": 3,
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

    

    

    
    
