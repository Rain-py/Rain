from Rain.Provisioner.LocalProvisioner import LocalProvisioner
from Rain.Provisioner.CloudProvisioner import CloudProvisioner

class ProvisionerFactory:
    @staticmethod
    def create_provisioner(config):    
        if config["mode"]["type"] == 'cloud':
            try:
                subscription_id = config["mode"]["params"]["subscription_id"]
                location = config["mode"]["params"]["location"]
            except Exception as e:
                raise Exception("Invalid provisioner config")
            return CloudProvisioner(subscription_id= subscription_id,
                                    location=location)
        elif config["mode"]["type"] == 'local':
            return LocalProvisioner()
        else:
            raise Exception("Invalid provisioner type")