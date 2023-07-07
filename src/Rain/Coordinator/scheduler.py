import itertools
from itertools import product
from tcppinglib import tcpping

from Rain.TemporaryFilesManager.TemporaryFilesManager import TemporaryFilesManager
from Rain.LogService.LogService import LogService

class Scheduler:
    def __init__(self):
        self.data_base_path = TemporaryFilesManager.get_instance().create_temp_dir('scheduler/')
        self.logger = LogService("Scheduler")

    def create_latency_matrix(instances):
        num_instances = len(instances)
        latency_matrix = [0 * num_instances for _ in range(num_instances)]
        IPs = instances
        for i in range(num_instances):
            host = tcpping(IPs[i], interval=1.5,port=443, count=3)
            latency_matrix[i] = host.avg_rtt
        print(latency_matrix)
        return latency_matrix
        
    # TODO : if partition > machine capacity

    def distribute(data,instances,machines_capacity, default = True):
        # uniform distribution
        # if default scheduler is used 
        # or all the instances have the same capacity and the capacity is greater than the data size, then distribute the data uniformly
        if default or (all(x == instances[0] for x in instances) and all(x == machines_capacity[0] for x in machines_capacity) and machines_capacity[0] >= max(data)):
            return [i%len(machines_capacity) for i in range(len(data))]

        # if the number of instances is equal to the number of data, sort the data and machines according to their size and assign each data to a machine
        elif len(data) == len(instances):
            # return index of the machine with the minimum difference between its capacity and the data size
            data_sorted = sorted(data)
            machines_capacity_sorted = sorted(machines_capacity)
            # return list of indices of the machines in the order of the data size
            group = [0] * len(data)
            for i in range(len(data)):
                index = data.index(data_sorted[i])
                machine_index = machines_capacity.index(machines_capacity_sorted[i])
                group[index] = machine_index
            return group

        # if the number of instances not equal to the number of data, then use the loss function to find the best group
        else:              
            latency_matrix = self.create_latency_matrix(instances)
            min_loss = float('inf')
            best_group = []
            unique_combinations = []
            output = list(product(data, range(len(machines_capacity))))


            for group in itertools.combinations(output,len(data)):
                print(group)
                data_size = {item[0] for item in group}
                machine_num = {item[1] for item in group}
                if len(data_size) == len(group) and all(item[0] <= machines_capacity[item[1]] for item in group) and not all( x == group[0][1] for x in machine_num):
                    unique_combinations.append(list(group))

            for group in unique_combinations:
                print(group)
                loss = 0
                unused_space = 0
                latency = sum(latency_matrix[item[1]] for item in group)
                for item in group:
                    print(item[1])
                    if item[0] > machines_capacity[item[1]]:
                        break
                    else:
                        unused_space += machines_capacity[item[1]] - item[0]
                
                loss = loss_function(latency, unused_space)
                print(loss)
                if loss < min_loss:
                    min_loss = loss
                    best_group = group
            
            return best_group

    def loss_function(predicted_latency, difference):
        return predicted_latency + ( 1/difference)

# data = [25,10,100]
# machines_capacity = [50,100,70]
# instances = ['127.0.0.1','127.0.0.1','127.0.0.1']
# partition = distribute(data,instances,machines_capacity,default=False)
# print(partition)
# result = ping('127.0.0.1', count=1)
# print('result.time ' + str(result.rtt_avg_ms))