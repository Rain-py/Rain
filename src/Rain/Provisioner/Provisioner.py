from Rain.Provisioner.ProvisionerAmbassador import ProvisionerAmbassador
from Rain.Provisioner.ProvisionerFactory import ProvisionerFactory
from Rain.Coordinator.Coordinator import Coordinator
from Rain.LogService.LogService import LogService


class Provisioner(ProvisionerAmbassador):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.logger = LogService("Provisioner")
        # create coordinator
        self.logger.log('debug', "Creating coordinator")
        self.coordinator = Coordinator(divider_IP='127.0.0.1', provisioner_IP= '127.0.0.1')
        try:
            self.provisioner = ProvisionerFactory.create_provisioner(self.config)
        except Exception as e:
            self.logger.log('error', f"Error creating provisioner: {e}")
            
        
    def __del__(self):
        try:
            del self.coordinator
            del self.provisioner
        except Exception as e:
            self.logger.log('error', f"Error deleting:{e}")
            return
    
    def start_coordinator(self):
        self.logger.log('debug', "Starting coordinator")
        self.coordinator.serve()

    def create_workers(self):
        self.provisioner.create_workers(self.get_num_workers())
        self.ids = self.provisioner.get_workers_ids()
        self.ips = self.provisioner.get_workers_ips()
        self.ports = self.provisioner.get_workers_ports()
        self.statuses = self.provisioner.get_workers_statuses()
        self.logger.log('debug', f"[Created workers]\nIPs : {self.ips}, ports: {self.ports}, statuses: {self.statuses}, IDs : {self.ids}")

    def delete_workers(self):
        self.provisioner.delete_workers()
        self.ids = self.provisioner.get_workers_ids()
        self.ips = self.provisioner.get_workers_ips()
        self.ports = self.provisioner.get_workers_ports()
        self.statuses = self.provisioner.get_workers_statuses()
        self.logger.log('debug', f"[Deleted workers]\nIPs : {self.ips}, ports: {self.ports}, statuses: {self.statuses}, IDs : {self.ids}")
    
    