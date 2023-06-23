
import sys
import os

sys.path.append('./Provisioner')
from Provisioner.Provisioner import Provisioner
sys.path.pop()

sys.path.append('./Divider')
from Divider.Divider import Divider
sys.path.pop()

class Rain:
    def __init__(self, config, model, X_train, y_train):
        self.provisioner = Provisioner(subscription_id= '82305756-d4a0-442d-8e73-625e1ced2113', # Nada's ID
                                       # Mostafa's ID 'a7ef3688-af58-4835-953c-e51f219fbd0f',
                                resource_group_name='Rain_resourcegroup',
                                location='eastus')
        self.divider = Divider(config, model, X_train, y_train)
        self.ip_addresses = []

    def __del__(self):
        del self.provisioner
        del self.divider

    def setup_vms(self):
        # Setup networking
        self.provisioner.setup_networking()
        # Creating the required keys
        private_key, public_key = self.provisioner.create_ssh_key_pair(
            private_key_path=os.path.join(os.path.dirname(__file__),
                                        'keys/private_key.pem'),
            public_key_path=os.path.join(os.path.dirname(__file__),
                                        'keys/public_key.pem'))

        # # Choose the vm based on the required specs
        # available_vm_sizes = self.provisioner.get_vms_by_specs(vcpu_count=1,
        #                                                         memory_gb=3.5)
        # vm_size = available_vm_sizes[0]['name']
        # print(f'VM size: {vm_size}')

        # Create the VMs
        custom_data_script1 = "#cloud-config\n\nruncmd:\n  - apt-get update\n  - apt-get install -y apache2\n  - echo 'Hello1' > /var/www/html/index.html"
        custom_data_script2 = "#cloud-config\n\nruncmd:\n  - apt-get update\n  - apt-get install -y apache2\n  - echo 'Hello2' > /var/www/html/index.html"
        self.provisioner.create_virtual_machine('Rain-vm1', 'Standard_DS1_v2', public_key,
                                        custom_data_script1)
        self.provisioner.create_virtual_machine('Rain-vm2', 'Standard_DS1_v2', public_key,
                                        custom_data_script2)
        ip_address1 = self.provisioner.get_ip_address_by_vm_name('Rain-vm1')
        ip_address2 = self.provisioner.get_ip_address_by_vm_name('Rain-vm2')
        self.ip_addresses.append(ip_address1)
        self.ip_addresses.append(ip_address2)
        return ip_address1, ip_address2
    def delete_vms(self):
        del self.provisioner

    def test(self):
        self.divider.send_data_to_workers()
        
    def train_centralized_sync(self):
        # connect vms
        # send data
        model = self.divider.train_centralized_sync()
        return model


    def train_centralized_async(self):
        model = self.divider.train_centralized_async()
        return model
    


    

    

    
    
