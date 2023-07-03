import dill
from Rain.Divider.Divider import Divider
from Rain.LogService.LogService import LogService
from Rain.Divider.DividerProxyAmbassador import DividerProxyAmbassador
from Rain.TemporaryFilesManager.TemporaryFilesManager import TemporaryFilesManager

class DividerProxy():
    def __init__(self, config, model):
        self.config = config
        self.model = model
        self.divider = Divider()
        self.logger = LogService("DividerProxy")
        self.divider_proxy_ambassador = DividerProxyAmbassador()  
        self.data_base_path = TemporaryFilesManager.get_instance().create_temp_dir('divider_proxy/')
      
    def __del__(self):
        del self.divider_proxy_ambassador
        del self.divider

    def serve(self):
        self.divider_proxy_ambassador.serve()

    def stop_serving(self):
        self.divider_proxy_ambassador.stop_serving()
        self.logger.log('debug', f"Divider Proxy stopped serving")
    
    def send_data_to_divider(self, X_train, y_train, model, config):

        try:
            self.divider_proxy_ambassador.send_data(X_train, y_train, model, config)
        except Exception as e:
            self.logger.log('debug', f"Error in sending data to divider: {e}")
            return

    def receive_model(self):
        try:
            model = dill.load(open(f"{self.data_base_path}model.pkl", "rb"))
            return model
        except Exception as e:
            self.logger.log('debug', f"Error in reading model in divider proxy: {e}")
            return


    def train(self, X_train, y_train, strategy='sync'):
        try:
            self.divider.serve()
            # send data to divider 
            self.logger.log('debug', f"Sending data to divider")
            self.send_data_to_divider(X_train, y_train, self.model, self.config)

            # train
            self.logger.log('debug', f"Training Started")
            # trigger training in divider
            self.divider.train(strategy)

            # get the model
            model = self.receive_model()
            self.divider.stop_serving()
            return model 

        except Exception as e:
            self.logger.log('error', f"Error in training: {e}")
            return None

