import os
import sys
from Divider.DividerAmbassador import DividerAmbassador
from Divider.DeepLearning.DeepLearningFactory import DeepLearningFactory

sys.path.append('../LogService')
from LogService.LogService import LogService
sys.path.pop()


class Divider:
    def __init__(self, model, config):
        self.num_of_workers = config["partitions"]
        self.logger = LogService("Divider")
        self.divider_ambassador = DividerAmbassador()

        # define the coord & provisioner IPs
        self.coordinator_IP = '127.0.0.1'
        self.provisioner_IP = '127.0.0.1'
        
        self.data_base_path = "../../../data/"
        self.model_base_path = "../../../Divider/divider/data/"
        if not os.path.exists(self.model_base_path):
            os.makedirs(self.model_base_path)

        # define the interface
        if config["learning_type"] == "DL":
            self.algorithm = DeepLearningFactory.create_DL_interface(model, config, self.divider_ambassador)
        elif config["learning_type"] == "ML":
            self.algorithm = None


    def serve(self):
        self.divider_ambassador.serve()


    def stop_serving(self):
        self.divider_ambassador.stop_serving()
        self.logger.log('debug', f"Divider stopped serving")


    def send_data_to_workers(self):
        try:
            self.divider_ambassador.send_data(self.coordinator_IP, self.provisioner_IP, self.num_of_workers, self.data_base_path)
        except Exception as e:
            self.logger.log('debug', f"Error in sending data to workers: {e}")
            return


    def send_info_to_workers(self, iteration_num):
        self.algorithm.send_info_to_workers(iteration_num)

    
    def train_centralized_sync(self):
        model = self.algorithm.train_centralized_sync()
        return model

    def train_centralized_async(self):
        model = self.algorithm.train_centralized_async()
        return model

    # destructor 
    def __del__(self):
        self.divider_ambassador.stop_serving()