from abc import ABC, abstractmethod

class ProvisionerInterface(ABC):
    @abstractmethod
    def create_workers(self, num_workers):
        pass
    
    @abstractmethod
    def delete_workers(self):
        pass
    
    @abstractmethod
    def get_workers_ids(self):
        pass
    
    @abstractmethod
    def get_workers_ips(self):
        pass
    
    @abstractmethod
    def get_workers_ports(self):
        pass
    
    @abstractmethod
    def get_workers_statuses(self):
        pass
