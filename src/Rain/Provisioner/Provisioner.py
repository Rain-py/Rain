from Rain.Provisioner.ProvisionerAmbassador import ProvisionerAmbassador
from Rain.Provisioner.ProvisionerFactory import ProvisionerFactory
from Rain.Coordinator.Coordinator import Coordinator
from Rain.LogService.LogService import LogService


class Provisioner(ProvisionerAmbassador):
    def __init__(self, config):
        Coordinator_IP = '127.0.0.1'
        super().__init__(Coordinator_IP)
        self.config = config
        self.logger = LogService("Provisioner")
        self.logger.log('debug', "Creating coordinator")
        self.coordinator = Coordinator(divider_IP='127.0.0.1', provisioner_IP= '127.0.0.1', num_of_workers = config["mode"]["params"]["num_of_workers"], num_partitions= config["partitions"])
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
        try:
            self.logger.log('debug', "Starting coordinator")
            self.coordinator.serve()
        except Exception as e:
            self.logger.log('error', f"Error starting coordinator: {e}")
            return

    def create_worker(self, worker_id)  -> None:
        try:
            self.provisioner.create_worker(worker_id)
            self.ids = self.provisioner.get_workers_ids()
            self.ips = self.provisioner.get_workers_ips()
            self.ports = self.provisioner.get_workers_ports()
            self.statuses = self.provisioner.get_workers_statuses()
            self.logger.log('debug', f"[Created new worker]\nIPs : {self.ips}, ports: {self.ports}, statuses: {self.statuses}, IDs : {self.ids}")
        except Exception as e:
            self.logger.log('error', f"Error creating workers: {e}")
            return

    def create_workers(self):
        try:
            self.provisioner.create_workers(self.get_num_workers())
            self.ids = self.provisioner.get_workers_ids()
            self.ips = self.provisioner.get_workers_ips()
            self.ports = self.provisioner.get_workers_ports()
            self.statuses = self.provisioner.get_workers_statuses()
            self.logger.log('debug', f"[Created workers]\nIPs : {self.ips}, ports: {self.ports}, statuses: {self.statuses}, IDs : {self.ids}")
        except Exception as e:
            self.logger.log('error', f"Error creating workers: {e}")
            return

    def delete_workers(self):
        try:
            self.provisioner.delete_workers()
        except Exception as e:
            self.logger.log('error', f"Error deleting workers: {e}")
            return