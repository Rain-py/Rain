from Rain.Provisioner.LocalProvisioner import LocalProvisioner
from Rain.Provisioner.CloudProvisioner import CloudProvisioner
from Rain.Provisioner.LazyProvisioner import LazyProvisioner

class ProvisionerFactory:
    @staticmethod
    def create_provisioner(config): 
        # create the provisioner based on the config
        setup = None
        # get the setup based on the learning type
        if config["learning_type"] == 'ML':
            setup = 'ML'
        elif config["learning_type"] == 'DL':
            if config["DL"]["lib"]["type"] == "tensorflow":
                setup = 'TF'
            elif config["DL"]["lib"]["type"] == "pytorch":
                setup = 'PT'  
            else: 
                raise Exception("Invalid DL library") 
        else:
            raise Exception("Invalid learning type")
        
        # create the provisioner based on the mode
        if config["mode"]["type"] == 'cloud':
            try:
                subscription_id = config["mode"]["params"]["subscription_id"]
                location = config["mode"]["params"]["location"]
            except Exception as e:
                raise Exception("Invalid provisioner config")
            return CloudProvisioner(subscription_id= subscription_id,
                                    location=location, setup=setup)
        elif config["mode"]["type"] == 'lazy':
            try:
                ips = config["mode"]["params"]["ips"]
                ports = config["mode"]["params"]["ports"]
                return LazyProvisioner(ips=ips, ports=ports)
            except Exception as e:
                raise Exception("Invalid provisioner config")
        elif config["mode"]["type"] == 'local':
            return LocalProvisioner(chunk_size=config["chunk_size"], setup=setup)
        else:
            raise Exception("Invalid provisioner type")