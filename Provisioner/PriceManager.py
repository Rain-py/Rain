
class PriceManager:

    def __init__(self, compute_client):
        self.compute_client = compute_client

    def get_vms_by_specs(self, location, vcpu_count, memory_gb):
        filtered_vms = []

        try:
            # Retrieve all available VM sizes
            vm_sizes = self.compute_client.virtual_machine_sizes.list(location)
            # Filter VM sizes based on specified criteria
            for vm_size in vm_sizes:
                if vcpu_count is not None and vm_size.number_of_cores == vcpu_count \
                and memory_gb is not None and (vm_size.memory_in_mb / 1024 == memory_gb):
                    filtered_vms.append(vm_size.serialize())
        except Exception as e:
            print(e)
            raise Exception("Error getting VMs by specs")

        return filtered_vms
