from Rain.Coordinator.CoordinatorAmbassador import CoordinatorAmbassador
from Rain.LogService.LogService import LogService
from Rain.TemporaryFilesManager.TemporaryFilesManager import TemporaryFilesManager
import os




## Coordinator class
class Coordinator(CoordinatorAmbassador):
    def __init__(self, divider_IP, provisioner_IP):
        super().__init__()
        self.logger = LogService("Coordinator")
        self.logger.log('debug', f"Coordinator is initialized")
        self.divider_IP = divider_IP  
        self.provisioner_IP = provisioner_IP
        self.server  = None
        self.data_base_path = TemporaryFilesManager.get_instance().create_temp_dir('coord/data/')

    def __del__(self):
        pass

    