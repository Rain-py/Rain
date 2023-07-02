

from Provisioner.Provisioner import Provisioner

from Divider.DividerProxy import DividerProxy

import sys
sys.path.append('../LogService')
from LogService.LogService import LogService
sys.path.pop()

class Rain:
    def __init__(self, config, model):
        self.logger = LogService("Rain")
        self.logger.log('debug', f"Rain is initialized")
        self.config = config
        self.provisioner = Provisioner(self.config['mode'])
        self.divider_proxy = DividerProxy(config, model)
        self.ip_addresses = []

    def __del__(self):
        del self.provisioner
        del self.divider_proxy
        
    def train_centralized_sync(self, X_train, y_train):
        # create workers
        self.logger.log('debug', f"Creating workers")
        self.provisioner.serve()
        model = self.divider_proxy.train_centralized_sync(X_train, y_train)    
        self.provisioner.stop_serving()  
        return model


    def train_centralized_async(self, X_train, y_train):
        self.logger.log('debug', f"Creating workers")
        self.provisioner.serve()
        model = self.divider_proxy.train_centralized_async(X_train, y_train) 
        self.provisioner.stop_serving()        
        return model
    


    

    

    
    
