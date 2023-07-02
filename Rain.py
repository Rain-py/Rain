

from Provisioner.Provisioner import Provisioner

from Divider.Divider import Divider


import multiprocessing as mp


class Rain:
    def __init__(self, config, model, X_train, y_train):
        print("Rain is initialized")
        self.config = config
        self.provisioner = Provisioner(self.config['mode'])
        self.divider = Divider(config, model)
        self.ip_addresses = []

    def __del__(self):
        del self.provisioner
        del self.divider
        
    def train_centralized_sync(self):
        # create workers
        print("Rain: Creating workers")
        self.provisioner.serve()
        # send data
        self.divider.serve()
        print("Rain: Sending data to workers")
        self.divider.send_data_to_workers()
        # train
        print("Rain: Training")
        model = self.divider.train_centralized_sync() 
        self.provisioner.stop_serving()  
        self.divider.stop_serving()     
        return model


    def train_centralized_async(self):
        self.divider.send_data_to_workers()
        model = self.divider.train_centralized_async()
        return model
    


    

    

    
    
