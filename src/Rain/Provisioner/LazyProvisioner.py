from Rain.Worker.WorkerAmbassador import WorkerAmbassador
from Rain.Protos import provisioner_pb2
from Rain.LogService.LogService import LogService
from Rain.Provisioner.ProvisionerInterface import ProvisionerInterface

class LazyProvisioner(ProvisionerInterface):
    def __init__(self, ips, ports):
        self.ips = ips 
        self.statuses = []
        self.ports = ports
        self.ids = []
        self.num_workers = len(ips)
        self.logger = LogService("LazyProvisioner")
        self.logger.log('info', f"Provisioner is initialized")
    
    def __del__(self):
        try:
            self.delete_workers()
        except Exception as e:
            self.logger.log('error', f"Error deleting:{e}")
            return

    def delete_workers(self):
        # self.logger.log('info', f"Delete your workers, please")  
        pass
    
    def create_workers(self, num_workers = None):
        self.logger.log('info', f"Creating {num_workers} workers")
        try:
            self.statuses = [provisioner_pb2.Status.UP] * self.num_workers
            self.ids = [i+1 for i in range(self.num_workers)]
        except Exception as e:
            self.logger.log('error', f"Error configuring the workers: {e}")
            return
        
    def get_workers_ids(self):
        return self.ids
    def get_workers_ips(self):
        return self.ips
    def get_workers_ports(self):
        return self.ports
    def get_workers_statuses(self):
        return self.statuses