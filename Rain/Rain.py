

from Rain.Provisioner.Provisioner import Provisioner
from Rain.Divider.DividerProxy import DividerProxy
from Rain.LogService.LogService import LogService

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

    def train(self, X_train, y_train, strategy='sync'):
        if strategy == 'sync':
            return self.train_centralized_sync(X_train, y_train)
        elif strategy == 'async':
            return self.train_centralized_async(X_train, y_train)
        
    def train_centralized_sync(self, X_train, y_train):
        # create workers
        self.logger.log('debug', f"Creating workers")
        self.provisioner.serve()
        model = self.divider_proxy.train(X_train, y_train, strategy='sync')    
        self.provisioner.stop_serving()  
        return model


    def train_centralized_async(self, X_train, y_train):
        self.logger.log('debug', f"Creating workers")
        self.provisioner.serve()
        model = self.divider_proxy.train(X_train, y_train, strategy='sync') 
        self.provisioner.stop_serving()        
        return model
    


    

    

    
    
