from Coordinator.CoordinatorAmbassador import CoordinatorAmbassador

import sys
import os

sys.path.append('../LogService')
from LogService.LogService import LogService
sys.path.pop()



## Coordinator class
class Coordinator(CoordinatorAmbassador):
    def __init__(self, divider_IP, provisioner_IP):
        super().__init__()
        self.logger = LogService("Coordinator")
        self.logger.log('debug', f"Coordinator is initialized")
        self.divider_IP = divider_IP  
        self.provisioner_IP = provisioner_IP
        self.server  = None
        self.base_path = '../../../Coordinator/coord/'
        self.data_base_path = self.base_path + 'data/'
        if not os.path.exists(self.data_base_path):
            os.makedirs(self.data_base_path) 

    def __del__(self):
        pass

    