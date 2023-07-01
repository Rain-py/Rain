from Provisioner.GlueProvisioner import GlueProvisioner
from Provisioner.LocalProvisioner import LocalProvisioner
from Provisioner.CloudProvisioner import CloudProvisioner

import sys
sys.path.append('../Coordinator')
from Coordinator.Coordinator import Coordinator
sys.path.pop()
import multiprocessing as mp

class Provisioner(GlueProvisioner):
    def __init__(self, mode):
        super().__init__()
        self.mode = mode
        # create coordinator
        print("Provisioner: Creating coordinator")
        self.coordinator = Coordinator(divider_IP='127.0.0.1', provisioner_IP= '127.0.0.1')
        if mode == 'cloud':
            self.provisioner = CloudProvisioner(subscription_id= '82305756-d4a0-442d-8e73-625e1ced2113', # Nada's ID
                                       # Mostafa's ID 'a7ef3688-af58-4835-953c-e51f219fbd0f',
                                resource_group_name='Rain_resourcegroup',
                                location='eastus')
        elif mode == 'local':
            self.provisioner = LocalProvisioner()
        else:
            raise Exception("Invalid provisioner type")
        
    def __del__(self):
        del self.coordinator
        del self.provisioner
    
    def start_coordinator(self):
        print("Provisioner: Starting coordinator")
        self.coordinator.serve()

    def create_workers(self):
        self.provisioner.create_workers(self.get_num_workers())
        self.ids = self.provisioner.get_workers_ids()
        self.ips = self.provisioner.get_workers_ips()
        self.ports = self.provisioner.get_workers_ports()
        self.statuses = self.provisioner.get_workers_statuses()
        print(f"[Created workers]\n IPs : {self.ips}, ports: {self.ports}, statuses: {self.statuses}, IDs : {self.ids}")

    def delete_workers(self):
        self.provisioner.delete_workers()
        self.ids = self.provisioner.get_workers_ids()
        self.ips = self.provisioner.get_workers_ips()
        self.ports = self.provisioner.get_workers_ports()
        self.statuses = self.provisioner.get_workers_statuses()
        print(f"[Deleted workers]\n IPs : {self.ips}, ports: {self.ports}, statuses: {self.statuses}, IDs : {self.ids}")
    
    