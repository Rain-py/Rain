from Provisioner.LocalProvisioner import LocalProvisioner
from Provisioner.CloudProvisioner import CloudProvisioner

class ProvisionerFactory:
    @staticmethod
    def create_provisioner(mode):    
        if mode == 'cloud':
                return CloudProvisioner(subscription_id= '82305756-d4a0-442d-8e73-625e1ced2113', # Nada's ID
                                        # Mostafa's ID 'a7ef3688-af58-4835-953c-e51f219fbd0f',
                                    resource_group_name='Rain_resourcegroup',
                                    location='eastus')
        elif mode == 'local':
            return LocalProvisioner()
        else:
            raise Exception("Invalid provisioner type")