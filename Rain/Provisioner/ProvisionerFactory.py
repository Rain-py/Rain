from Rain.Provisioner.LocalProvisioner import LocalProvisioner
from Rain.Provisioner.CloudProvisioner import CloudProvisioner

class ProvisionerFactory:
    @staticmethod
    def create_provisioner(config):    
        if config["mode"]["type"] == 'cloud':
            try:
                subscription_id = config["mode"]["params"]["subscription_id"]
                resource_group_name = config["mode"]["params"]["resource_group_name"]
                location = config["mode"]["params"]["location"]
            except Exception as e:
                raise Exception("Invalid provisioner config")
            return CloudProvisioner(subscription_id= subscription_id,
                                    resource_group_name=resource_group_name,
                                    location=location)
        elif config["mode"]["type"] == 'local':
            return LocalProvisioner()
        else:
            raise Exception("Invalid provisioner type")