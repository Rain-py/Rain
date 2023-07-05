from Rain.Provisioner.LocalProvisioner import LocalProvisioner
from Rain.Provisioner.CloudProvisioner import CloudProvisioner
from Rain.Provisioner.LazyProvisioner import LazyProvisioner

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
        elif config["mode"]["type"] == 'onPremise':
            try:
                ips = config["mode"]["params"]["ips"]
                ports = config["mode"]["params"]["ports"]
                return LazyProvisioner(ips=ips, ports=ports)
            except Exception as e:
                raise Exception("Invalid provisioner config")
        elif config["mode"]["type"] == 'local':
            return LocalProvisioner()
        else:
            raise Exception("Invalid provisioner type")