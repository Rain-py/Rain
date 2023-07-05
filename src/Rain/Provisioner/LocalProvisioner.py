
from Rain.Worker.WorkerAmbassador import WorkerAmbassador
from Rain.Protos import provisioner_pb2
from Rain.LogService.LogService import LogService
from Rain.Provisioner.ProvisionerInterface import ProvisionerInterface


BASE_PORT = 50151


class LocalProvisioner(ProvisionerInterface):
    def __init__(self):
        self.ips = [] 
        self.statuses = []
        self.ports = []
        self.ids = []
        self.workers = []
        self.num_workers = 0
        self.logger = LogService("LocalProvisioner")
        self.logger.log('debug', f"Provisioner is initialized")
    
    def __del__(self):
        try:
            self.delete_workers()
        except Exception as e:
            self.logger.log('error', f"Error deleting:{e}")
            return

    def delete_workers(self):
        for worker in self.workers:
            worker.stop_serving()
            del worker
        self.logger.log('debug', f"Workers are deleted")      
    
    def create_workers(self, num_workers):
        self.logger.log('debug', f"Creating {num_workers} workers")
        self.num_workers = num_workers
        try:
            self.ips = ['127.0.0.1'] * self.num_workers
            self.ports = [i+BASE_PORT for i in range(self.num_workers)]
            self.ids = [i+1 for i in range(self.num_workers)]
        except Exception as e:
            self.logger.log('error', f"Error configuring the workers: {e}")
            return
        
        try:
            for i in range(self.num_workers):
                worker = WorkerAmbassador(self.ports[i])
                worker.serve()
                self.workers.append(worker)
            self.statuses = [provisioner_pb2.Status.UP] * self.num_workers
            return self.workers
        except Exception as e:
            self.logger.log('error', f"Error creating the workers: {e}")
            return
    
    def get_workers_ids(self):
        return self.ids
    def get_workers_ips(self):
        return self.ips
    def get_workers_ports(self):
        return self.ports
    def get_workers_statuses(self):
        return self.statuses