import sys
sys.path.append('../')
from Worker.worker import worker
from protos import provisioner_pb2
sys.path.pop()

BASE_PORT = 50151


class LocalProvisioner():
    def __init__(self):
        self.ips = [] 
        self.statuses = []
        self.ports = []
        self.ids = []
        self.workers = []
        self.num_workers = 0
        print("LocalProvisioner is initialized")
    def __del__(self):
        self.delete_workers()
    
    def create_workers(self, num_workers):
        print("LocalProvisioner: Creating workers")
        self.num_workers = num_workers
        try:
            self.ips = ['127.0.0.1'] * self.num_workers
            self.statuses = [provisioner_pb2.Status.UP] * self.num_workers
            self.ports = [i+BASE_PORT for i in range(self.num_workers)]
            self.ids = [i+1 for i in range(self.num_workers)]
        except Exception as e:
            print("Error configuring the workers: ", e)
            return
        
        try:
            for i in range(self.num_workers):
                worker_instance = worker(self.ports[i])
                worker_instance.serve()
                self.workers.append(worker_instance)
            return self.workers
        except Exception as e:
            print("Error creating the workers: ", e)
            return
    def delete_workers(self):
        del self.workers        
    def get_workers_ids(self):
        return self.ids
    def get_workers_ips(self):
        return self.ips
    def get_workers_ports(self):
        return self.ports
    def get_workers_statuses(self):
        return self.statuses