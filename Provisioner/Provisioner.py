from GlueProvisioner import GlueProvisioner
from LocalProvisioner import LocalProvisioner
from CloudProvisioner import CloudProvisioner

class Provisioner(GlueProvisioner):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.provisioner = None
        if self.config['mode'] == 'cloud':
            self.provisioner = CloudProvisioner(subscription_id= '82305756-d4a0-442d-8e73-625e1ced2113', # Nada's ID
                                       # Mostafa's ID 'a7ef3688-af58-4835-953c-e51f219fbd0f',
                                resource_group_name='Rain_resourcegroup',
                                location='eastus')
        elif self.config['mode'] == 'local':
            self.provisioner = LocalProvisioner()
        else:
            raise Exception("Invalid provisioner type")
        
    def __del__(self):
        del self.provisioner
        
    def create_workers(self):
        self.provisioner.create_workers(self.get_num_workers())
        self.ids = self.provisioner.get_workers_ids()
        self.ips = self.provisioner.get_workers_ips()
        self.ports = self.provisioner.get_workers_ports()
        self.statuses = self.provisioner.get_workers_statuses()
        print(f"[create_workers]Status\n IPs : {self.ips}, ports: {self.ports}, statuses: {self.statuses}, IDs : {self.ids}")

    def delete_workers(self):
        self.provisioner.delete_workers()
        self.ids = self.provisioner.get_workers_ids()
        self.ips = self.provisioner.get_workers_ips()
        self.ports = self.provisioner.get_workers_ports()
        self.statuses = self.provisioner.get_workers_statuses()
        print(f"[delete_workers]Status\n IPs : {self.ips}, ports: {self.ports}, statuses: {self.statuses}, IDs : {self.ids}")

if __name__ == '__main__':
    config = {
        'mode': 'local'
    }
    provisioner = Provisioner(config)
    provisioner.serve()
    