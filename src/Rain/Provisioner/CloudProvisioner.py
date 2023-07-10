import base64
import socket
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.compute.models import (HardwareProfile, LinuxConfiguration,
                                       OSProfile)
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient

from Rain.Protos import provisioner_pb2
from Rain.LogService.LogService import LogService
from Rain.Provisioner.ProvisionerInterface import ProvisionerInterface
from Rain.TemporaryFilesManager.TemporaryFilesManager import TemporaryFilesManager


BASE_PORT = 50151
class CloudProvisioner(ProvisionerInterface):

    ############## Constructors ##############
    def __init__(self, subscription_id, location, vm_size = 'Standard_B2ms', chunk_size=1024*1024, setup='ML'):
        # credentials
        try:
            credentials = DefaultAzureCredential()
        except Exception as e:
            self.logger.log('error', f"Make sure you are authenticated with Azure:{e}")
            raise Exception("Make sure you are authenticated with Azure")

        # Management Clients
        try:
            self.compute_client = ComputeManagementClient(
                credentials, subscription_id)
            self.resource_client = ResourceManagementClient(
                credentials, subscription_id)
            self.network_client = NetworkManagementClient(
                credentials, subscription_id)
        except Exception as e:
            self.logger.log('error', f"Make sure you have the correct permissions:{e}")            
            raise Exception("Make sure you have the correct permissions")
        
        self.ips = [] 
        self.statuses = []
        self.ports = []
        self.ids = []
        self.num_workers = 0
        self.data_base_path = TemporaryFilesManager.get_instance().create_temp_dir('prov/')

        # For the internal use only
        self.location = location
        self.subnet = None
        self.nsg = None
        self.nic = None
        self.resource_group_name = 'Rain-resourcegroup'
        self.vnet_name = 'Rain-vnet'
        self.nic_name = 'Rain-nic'
        self.vm_name = 'Rain-vm'
        self.nsg_name = f'{self.nic_name}-nsg'
        self.nic_name_list = []
        self.ip_name_list = []
        self.vm_name_list = []
        # TODO: should be a parameter/temporary variable
        self.vm_size = vm_size

        # The custom data script
        tf_lib = setup == 'TF' 
        torch_lib = setup == 'PT'
        setup_script = "#cloud-config\n\nruncmd:\n  - sudo apt-get update\n  - sudo apt-get install -y apache2\n  - sudo apt install -y python3-pip\n  - sudo git clone https://gist.github.com/Mostafa-wael/ebd011579b7120e336e58671e5239248\n  - echo 'Installing...' > /var/www/html/index.html\n  - cd /ebd011579b7120e336e58671e5239248\n  - sudo chmod 777 setup.sh\n  - sudo ./setup.sh\n  - echo 'Done Installing Rain' > /var/www/html/index.html\n"
        install_tf_script = "  - sudo pip install keras>=2.12,<2.13\n  - sudo pip install tensorflow==2.12.0\n"
        install_torch_script = "  - sudo pip install torch==2.0.1\n"
        start_rain_worker = f"  - echo 'Worker is running...' > /var/www/html/index.html\n  - sudo start_rain_worker --chunk_size {chunk_size} --setup {setup}\n"
        self.custom_data_script = setup_script + install_tf_script * tf_lib + install_torch_script * torch_lib + start_rain_worker

        self.logger = LogService("CloudProvisioner")
        self.logger.log('info', f"Provisioner is initialized")
    ############## Destructors ##############
    def __del__(self):
        try:
            self.delete_workers()
        except Exception as e:
            self.logger.log('error', f"Error deleting:{e}")
            return
    ############## Resources Creation ##############
    def create_resource_group(self):
        try:
            self.resource_client.resource_groups.create_or_update(
                self.resource_group_name, {'location': self.location})
        except Exception as e:
            self.logger.log('error', f"Error creating resource group:{e}")            
            raise Exception("Error creating resource group")
        self.logger.log('info', f"Created resource group: {self.resource_group_name}")

    def create_virtual_network(self, vnet_name):
        vnet_params = {
            'address_space': {
                'address_prefixes': ['10.0.0.0/16']
            },
            'subnets': [{
                'name': 'Rain_subnet',
                'address_prefix': '10.0.0.0/24'
            }]
        }
        try:
            virtual_network_poller = self.network_client.virtual_networks.begin_create_or_update(
                self.resource_group_name, vnet_name, {
                    'location': self.location,
                    'address_space': vnet_params['address_space'],
                    'subnets': vnet_params['subnets']
                })
            virtual_network = virtual_network_poller.result()
        except Exception as e:
            self.logger.log('error', f"Error creating virtual network:{e}")            
            raise Exception("Error creating virtual network")
        self.logger.log('info', f"Created virtual network: {virtual_network.name}")

        try:
            subnet = self.network_client.subnets.get(self.resource_group_name,
                                                     virtual_network.name,
                                                     'Rain_subnet')
        except Exception as e:
            self.logger.log('error', f"Error getting subnet:{e}")            
            raise Exception("Error getting subnet")
        return subnet

    def create_network_security_group(self, network_security_group_name):
        # Add inbound security rules for ports 80 and 22
        security_rule_grpc = {
            'name': 'grpc',
            'protocol': 'Tcp',
            'destination_port_range': f'{BASE_PORT}',
            'destinationAddressPrefix': '*',
            'access': 'Allow',
            'direction': 'Inbound',
            'priority': 100,
            'source_address_prefix': '*',
            'source_port_range': '*'
        }
        security_rule_ssh = {
            'name': 'ssh',
            'protocol': 'Tcp',
            'destination_port_range': '22',
            'destinationAddressPrefix': '*',
            'access': 'Allow',
            'direction': 'Inbound',
            'priority': 101,
            'source_address_prefix': '*',
            'source_port_range': '*'
        }
        security_rule_http = {
            'name': 'http',
            'protocol': 'Tcp',
            'destination_port_range': '80',
            'destinationAddressPrefix': '*',
            'access': 'Allow',
            'direction': 'Inbound',
            'priority': 102,
            'source_address_prefix': '*',
            'source_port_range': '*'
        }
        security_rules = [security_rule_ssh, security_rule_http, security_rule_grpc]
        nsg_params = {
            'location': self.location,
            'security_rules': security_rules
        }
        try:
            nsg_poller = self.network_client.network_security_groups.begin_create_or_update(
                self.resource_group_name, network_security_group_name,
                nsg_params)
            nsg = nsg_poller.result()  # Get the actual NSG object
        except Exception as e:
            self.logger.log('error', f"Error creating network security group:{e}")            
            raise Exception("Error creating network security group")
        self.logger.log('info', f"Created network security group: {nsg.name}")
        return nsg

    def setup_networking(self):
        try:
            self.create_resource_group()
            self.subnet = self.create_virtual_network(self.vnet_name)
            self.nsg = self.create_network_security_group(self.nsg_name)
        except Exception as e:
            self.logger.log('error', f"Error setting up networking:{e}")            
            raise Exception("Error setting up networking")
        self.logger.log('info', f"Network setup completed")


    def create_public_ip_address(self, public_ip_name):
        public_ip_params = {
            'public_ip_allocation_method': 'Dynamic',
            'location': self.location,
        }
        try:
            public_ip_poller = self.network_client.public_ip_addresses.begin_create_or_update(
                self.resource_group_name, public_ip_name, public_ip_params)
            public_ip = public_ip_poller.result(
            )  # Get the actual public IP object
            self.logger.log('debug', f'Created public IP address: {public_ip.name}')

            # add to list
            self.ip_name_list.append(public_ip.name)
        except Exception as e:
            self.logger.log('error', f"Error creating public ip address:{e}")            
            raise Exception("Error creating public ip address")
        return public_ip

    def create_network_interface(self, network_interface_name, subnet, nsg):
        try:
            public_ip_address = self.create_public_ip_address(
                                f'{network_interface_name}-ip')
            nic_poller = self.network_client.network_interfaces.begin_create_or_update(
                self.resource_group_name, network_interface_name, {
                    'location':
                    self.location,
                    'ip_configurations': [{
                        'name': 'Rain_ipconfig',
                        'subnet': {
                            'id': subnet.id
                        },
                        'public_ip_address': {
                            'id': public_ip_address.id
                        }
                    }],
                    'network_security_group': {
                        'id': nsg.id
                    }
                })
            nic = nic_poller.result()  # Get the actual NIC object
        except Exception as e:
            self.logger.log('error', f"Error creating network interface:{e}")            
            raise Exception("Error creating network interface")
        self.logger.log('info', f"Created network interface: {nic.name}")
        # add to list
        self.nic_name_list.append(nic.name)
        return nic

    def create_virtual_machine(self, virtual_machine_name, vm_size,
                               custom_data_script):
        # Create the image reference
        image_reference = {
            'publisher': 'Canonical',
            'offer'    :"0001-com-ubuntu-server-focal",
            'sku': '20_04-lts-gen2',
            'version': 'latest'
        }
        # Set the admin username and password for the VM
        admin_username = 'rain'
        admin_password = 'passw0rd#1'
        custom_data_encoded = base64.b64encode(
            custom_data_script.encode()).decode('utf-8')
        # Create the OS profile for the VM
        try:
            os_profile = OSProfile(computer_name=virtual_machine_name,
                                   admin_username=admin_username,
                                   admin_password=admin_password,
                                   custom_data=custom_data_encoded,
                                   linux_configuration=LinuxConfiguration(
                                       disable_password_authentication=False))
        except Exception as e:
            self.logger.log('error', f"Error creating OS profile:{e}")            
            raise Exception("Error creating OS profile")

        try:
            vm_poller = self.compute_client.virtual_machines.begin_create_or_update(
                self.resource_group_name, virtual_machine_name, {
                    'location': self.location,
                    'hardware_profile': HardwareProfile(vm_size=vm_size),
                    'os_profile': os_profile,
                    'storage_profile': {
                        'image_reference': image_reference
                    },
                    'network_profile': {
                        'network_interfaces': [{
                            'id':
                            self.create_network_interface(
                                f'{self.nic_name}-{virtual_machine_name}',
                                self.subnet, self.nsg).id,
                            'primary':
                            True
                        }]
                    }
                })
            vm = vm_poller.result()  # Get the actual VM object
            # add to list
            self.vm_name_list.append(vm.name)
        except Exception as e:
            self.logger.log('error', f"Error creating virtual machine:{e}")            
            raise Exception("Error creating virtual machine")
        self.logger.log('info', f"Created virtual machine: {vm.name}. You can access the machine using the following credentials: username: {admin_username}, password: {admin_password}")
        return vm

    ############## Resources Deletion ##############
    def delete_resource_group(self):
        self.logger.log('info', f"Deleting resource group: {self.resource_group_name}")
        self.resource_client.resource_groups.begin_delete(
            self.resource_group_name).wait()

    def delete_virtual_network(self):
        self.logger.log('info', f"Deleting virtual network: {self.vnet_name}")
        self.network_client.virtual_networks.begin_delete(
            self.resource_group_name, self.vnet_name).wait()

    def delete_network_security_group(self):
        self.logger.log('info', f"Deleting network security group: {self.nsg_name}")
        self.network_client.network_security_groups.begin_delete(
            self.resource_group_name, self.nsg_name).wait()

    def delete_networking(self):
        try:
            # Delete the network security group
            self.delete_network_security_group()
            # Delete the virtual network
            self.delete_virtual_network()
            # Delete the resource group
            self.delete_resource_group()
        except Exception as e:
            self.logger.log('error', f"Error deleting networking:{e}")            
            raise Exception("Error deleting networking")

        self.logger.log('debug', 'Networking cleanup completed')

    def delete_network_interface(self, nic_name):
        self.logger.log('info', f"Deleting network interface: {nic_name}")
        self.network_client.network_interfaces.begin_delete(
            self.resource_group_name, nic_name).wait()

    def delete_public_ip_address(self, public_ip_name):
        self.logger.log('info', f"Deleting public IP address: {public_ip_name}")
        self.network_client.public_ip_addresses.begin_delete(
            self.resource_group_name, public_ip_name).wait()

    def delete_virtual_machine(self, virtual_machine_name):
        self.logger.log('info', f"Deleting virtual machine: {virtual_machine_name}")
        self.compute_client.virtual_machines.begin_delete(
            self.resource_group_name, virtual_machine_name).wait()

    ############## Utility Methods ############## 
    def get_ip_address_by_vm_name(self, vm_name):
        try:
            # Get the public IP address
            public_ip_address = self.network_client.public_ip_addresses.get(
                self.resource_group_name, self.ip_name_list[self.vm_name_list.index(vm_name)])
        except Exception as e:
            self.logger.log('error', f"Error getting IP address by VM name:{e}")            
            raise Exception("Error getting IP address by VM name")

        return public_ip_address.ip_address
    
    ############## Rain Methods ############## 
    def delete_workers(self):
        try:
            # iterate over the vms and delete them
            for idx, vm_name in enumerate(self.vm_name_list):
                # delete the vm
                self.delete_virtual_machine(vm_name)

                # get the nic at that index
                nic_name = self.nic_name_list[idx]
                # delete the nic
                self.delete_network_interface(nic_name)

                # get the public ip at that index
                ip_name = self.ip_name_list[idx]
                # delete the public ip
                self.delete_public_ip_address(ip_name)
            # empty the lists
            self.vm_name_list = []
            self.nic_name_list = []
            self.ip_name_list = []
            self.ips = [] 
            self.statuses = []
            self.ports = []
            self.ids = []

        except Exception as e:
            self.logger.log('error', f"Error deleting VMs:{e}")
            raise Exception("Error deleting VMs")
        try:
            self.delete_networking()
        except Exception as e:
            self.logger.log('error', f"Error deleting networking:{e}")
            raise Exception("Error deleting networking")
        self.logger.log('info', f"Workers are deleted")      

    def create_workers(self, num_workers):
        self.num_workers = num_workers
        try:
            self.logger.log('info',"Setup the networking for the workers")
            self.setup_networking()
        except Exception as e:
            self.logger.log('error', f"Error setting up networking: {e}, please check azure: https://portal.azure.com/#home")
            return
        self.logger.log('info', f"Creating {self.num_workers} worker{'' if self.num_workers==1 else 's'}")
        try:
            for i in range(num_workers):
                self.logger.log('debug', f'Creating worker {self.vm_name}{i+1}')
                self.create_virtual_machine(f'{self.vm_name}{i+1}', self.vm_size,
                                        self.custom_data_script)
                self.ids.append(i+1)
                self.logger.log('info', f"Created worker {self.vm_name}{i+1}")
        except Exception as e:
            self.logger.log('error', f"Error creating the workers: {e}")
            return
        try:
            for i in range(num_workers):
                ip = self.get_ip_address_by_vm_name(f'{self.vm_name}{i+1}')
                self.ips.append(ip)
                self.ports.append(BASE_PORT)
                while self.get_worker_port_status(ip) != provisioner_pb2.Status.UP:
                    continue
                self.statuses.append(provisioner_pb2.Status.UP)
                self.logger.log('info', f"Worker {i+1} is up on {ip}:{BASE_PORT}")
        except Exception as e:
            self.logger.log('error', f"Error getting the workers IPs: {e}")
            return
            
    def get_workers_ids(self):
        return self.ids
    def get_workers_ips(self):
        return self.ips
    def get_workers_ports(self):
        return self.ports
    def get_workers_statuses(self):
        return self.statuses

    def get_worker_port_status(self, ip):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)  # Set a timeout value for the connection attempt
            result = sock.connect_ex((ip, BASE_PORT))
            sock.close()
            if result == 0:
                return provisioner_pb2.Status.UP
            else:
                return provisioner_pb2.Status.DOWN
        except socket.error as e:
            self.logger.log('error', f"Error getting the port statuses of the worker with ip: {ip}: {e}")