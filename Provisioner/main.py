import os
from Provisioner.Provisioner import Provisioner

if __name__ == '__main__':
    try:
        # initializations
        subscription_id = 'a7ef3688-af58-4835-953c-e51f219fbd0f'
        provisioner = Provisioner(subscription_id=subscription_id,
                                resource_group_name='Rain_resourcegroup',
                                location='eastus')

        # Setup networking
        provisioner.setup_networking()

        # Creating the required keys
        private_key, public_key = provisioner.create_ssh_key_pair(
            private_key_path=os.path.join(os.path.dirname(__file__),
                                        'private_key.pem'),
            public_key_path=os.path.join(os.path.dirname(__file__),
                                        'public_key.pem'))

        # Choose the vm based on the required specs
        available_vm_sizes = provisioner.get_vms_by_specs(vcpu_count=1,
                                                                memory_gb=0.5)
        vm_size = available_vm_sizes[0]['name']
        print(f'VM size: {vm_size}')

        # Create the VMs
        custom_data_script1 = "#cloud-config\n\nruncmd:\n  - apt-get update\n  - apt-get install -y apache2\n  - echo 'Hello1' > /var/www/html/index.html"
        custom_data_script2 = "#cloud-config\n\nruncmd:\n  - apt-get update\n  - apt-get install -y apache2\n  - echo 'Hello2' > /var/www/html/index.html"
        provisioner.create_virtual_machine('Rain-vm1', vm_size, public_key,
                                        custom_data_script1)
        provisioner.create_virtual_machine('Rain-vm2', vm_size, public_key,
                                        custom_data_script2)
        ip_address1 = provisioner.get_ip_address_by_vm_name('Rain-vm1')
        ip_address2 = provisioner.get_ip_address_by_vm_name('Rain-vm2')
        print(f'VM1 IP address: {ip_address1}')
        print(f'VM2 IP address: {ip_address2}')

        # logic
        if input('Delete the resources? (y/n)') == 'y':
            # When the Provisioner object is no longer needed, it will automatically delete the resources
            del provisioner
    except Exception as e:
        print(e)
        del provisioner