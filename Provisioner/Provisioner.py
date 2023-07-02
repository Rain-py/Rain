from Provisioner.ProvisionerAmbassador import ProvisionerAmbassador
from Provisioner.LocalProvisioner import LocalProvisioner
from Provisioner.CloudProvisioner import CloudProvisioner

import sys
sys.path.append('../Coordinator')
from Coordinator.Coordinator import Coordinator
sys.path.pop()

sys.path.append('../LogService')
from LogService.LogService import LogService
sys.path.pop()


class Provisioner(ProvisionerAmbassador):
    def __init__(self, mode):
        super().__init__()
        self.mode = mode
        # create coordinator
        LogService.get_instance().log('debug', "Creating coordinator")
        self.coordinator = Coordinator(divider_IP='127.0.0.1', provisioner_IP= '127.0.0.1')
        if mode == 'cloud':
            self.provisioner = CloudProvisioner(subscription_id= '82305756-d4a0-442d-8e73-625e1ced2113', # Nada's ID
                                       # Mostafa's ID 'a7ef3688-af58-4835-953c-e51f219fbd0f',
                                resource_group_name='Rain_resourcegroup',
                                location='eastus')
        elif mode == 'local':
            self.provisioner = LocalProvisioner()
        else:
            LogService.get_instance().log('error', "Invalid provisioner type")
            raise Exception("Invalid provisioner type")
        
    def __del__(self):
        del self.coordinator
        del self.provisioner
    
    def start_coordinator(self):
        LogService.get_instance().log('debug', "Starting coordinator")
        self.coordinator.serve()

    def create_workers(self):
        self.provisioner.create_workers(self.get_num_workers())
        self.ids = self.provisioner.get_workers_ids()
        self.ips = self.provisioner.get_workers_ips()
        self.ports = self.provisioner.get_workers_ports()
        self.statuses = self.provisioner.get_workers_statuses()
        LogService.get_instance().log('debug', f"[Created workers]\nIPs : {self.ips}, ports: {self.ports}, statuses: {self.statuses}, IDs : {self.ids}")

    def delete_workers(self):
        self.provisioner.delete_workers()
        self.ids = self.provisioner.get_workers_ids()
        self.ips = self.provisioner.get_workers_ips()
        self.ports = self.provisioner.get_workers_ports()
        self.statuses = self.provisioner.get_workers_statuses()
        LogService.get_instance().log('debug', f"[Deleted workers]\nIPs : {self.ips}, ports: {self.ports}, statuses: {self.statuses}, IDs : {self.ids}")
    
    