

from Provisioner.Provisioner import Provisioner

from Divider.Divider import Divider

import sys
sys.path.append('../LogService')
from LogService.LogService import LogService
sys.path.pop()

class Rain:
    def __init__(self, config, model, X_train, y_train):
        self.logger = LogService("Rain")
        self.logger.log('debug', f"Rain is initialized")
        self.config = config
        self.provisioner = Provisioner(self.config['mode'])
        self.divider = Divider(config, model)
        self.ip_addresses = []

    def __del__(self):
        del self.provisioner
        del self.divider
        
    def train_centralized_sync(self):
        # create workers
        self.logger.log('debug', f"Creating workers")
        self.provisioner.serve()
        self.divider.serve()
        # send data
        # train
        self.logger.log('debug', f"Training")
        model = self.divider.train_centralized_sync() 
        self.provisioner.stop_serving()  
        self.divider.stop_serving()     
        return model


    def train_centralized_async(self):
        self.logger.log('debug', f"Creating workers")
        self.provisioner.serve()
        # send data
        self.divider.serve()
        # self.logger.log('debug', f"Sending data to workers")
        # self.divider.send_data_to_workers()
        # train
        self.logger.log('debug', f"Training")
        model = self.divider.train_centralized_async() 
        self.provisioner.stop_serving()  
        self.divider.stop_serving()     
        return model
    


    

    

    
    
