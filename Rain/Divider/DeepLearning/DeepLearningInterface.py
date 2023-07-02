import sys
import dill
import threading
import os
from abc import abstractmethod

from Rain.LogService.LogService import LogService

class DeepLearningInterface:
    def __init__(self, model, config, divider_ambassador):
        self.config = config
        self.lr = config["lr"]
        self.optimizer = config["optimizer"]
        self.loss = config["loss"]
        self.iterations = config["iterations"]
        self.partitions = config["partitions"]
        self.num_of_workers = config["partitions"]
        self.model = model

        self.logger = LogService("DeepLearning")
        self.divider_ambassador = divider_ambassador        

        # define the coord ip
        self.coordinator_IP = '127.0.0.1'

        # define the provisioner ip
        self.provisioner_IP = '127.0.0.1'
        
        self.model_base_path = "../../../../Rain/Divider/divider/data/"
        if not os.path.exists(self.model_base_path):
            os.makedirs(self.model_base_path) 
            

    def save_model(self, iteration_num):
        data = [{"config": self.config, "model": self.model}]
        file_path = f"{self.model_base_path}{iteration_num}.pkl"
        try:
            # save the data to the file        
            with open(file_path, "wb") as f:
                dill.dump(data, f)
        except Exception as e:
            self.logger.log('debug', f"Error in saving the info to the file: {e}")
            return

    # ________________________ Synchronous Training ________________________

    def receive_gradients_sync(self, partitions, iteration_num):
        gradients = []
        try:
            for j in range(partitions):
                msg = dill.load(open(f"{self.model_base_path}{j + 1}_{iteration_num}_trained.pkl", "rb"))
                gradients.append(msg)
        except Exception as e:
            self.logger.log('debug', f"Error in receiving the gradients from the workers: {e}")
            return
        return gradients
    
    
    @abstractmethod
    def reduce_gradients_sync(self, gradients):
        pass

    
    def train_centralized_sync(self):
        try:  
            # get the workers info from coordinator
            self.workers_IPs, self.workers_ports, self.workers_ids = self.divider_ambassador.get_workers_info(self.coordinator_IP)
            self.data_status = [0] * len(self.workers_IPs) # 0 means no data sent yet, 1 means data is already sent to the workers
        
            for i in range(self.iterations):   
                self.logger.log('debug', f"Starting iteration {i + 1}/{self.iterations}")
                # Notice, the algo.py is stateless
                self.save_model(i+1) #self.partitions,
                threads = list()
                for j in range(self.partitions): # note to be considered number of workers != number of partitions
                    thread = threading.Thread(target=self.divider_ambassador.iteration, args=(self.workers_ids[j], self.workers_IPs[j], self.workers_ports[j], self.data_status[j], i+1, i+1))
                    if i == 0:
                        self.data_status[j] = 1
                    threads.append(thread)
                    thread.start()
                for thread in threads:
                    thread.join()
                # self.divider_ambassador.iteration(self.coordinator_IP, i+1) # start loop
                gradients = self.receive_gradients_sync(self.partitions, i+1)
                self.reduce_gradients_sync(gradients)
                self.logger.log('debug', f"Iteration {i + 1}/{self.iterations} complete.")
            return self.model
        except Exception as e:
            self.logger.log('debug', f"Error in training the model: {e}")
            return

    # ________________________________________________________________________ 


    # ________________________ Asynchronous Training ________________________

    def receive_gradients_async(self, worker_id, iteration_num):
        gradients = None
        try:
            msg = dill.load(open(f"{self.model_base_path}{worker_id}_{iteration_num}_trained.pkl", "rb"))
            gradients = msg
        except Exception as e:
            print(f"Error in receiving the gradients from the workers: {e}")
            return
        return gradients
    
    
    @abstractmethod
    def reduce_gradients_async(self, gradient, worker_id):
        pass


    def worker_process_async(self, worker_id):
        # get the workers info from coordinator
        self.workers_IPs, self.workers_ports, self.workers_ids = self.divider_ambassador.get_workers_info(self.coordinator_IP)
        self.data_status = [0] * len(self.workers_IPs) # 0 means no data sent yet, 1 means data is already sent to the workers
        
        for i in range(self.iterations):
            self.logger.log('debug', f"Starting iteration {i + 1}/{self.iterations}")  
            self.divider_ambassador.iteration(self.workers_ids[worker_id], self.workers_IPs[worker_id], self.workers_ports[worker_id], self.data_status[worker_id], i+1, self.workers_ids[worker_id])
            if i == 0: # sending data (x_train , y_train) to workers only once
                self.data_status[worker_id] = 1

            gradient = self.receive_gradients_async(worker_id + 1,worker_id + 1) # worker_id, worker_id
            self.reduce_gradients_async(gradient, worker_id + 1)
            self.save_model(worker_id + 1) 
            self.logger.log('debug', f"Iteration {i + 1}/{self.iterations} complete for worker {worker_id + 1}.")
        
    
    def train_centralized_async(self):
        try:
            for id in range(self.num_of_workers):
                self.save_model(id + 1)

            threads = list()
            for id in range(self.num_of_workers):
                thread = threading.Thread(target=self.worker_process_async, args=(id,))
                threads.append(thread)
                thread.start()
            
            # wait for all threads to finish then return the model
            for thread in threads:
                thread.join()
            
            return self.model

        except Exception as e:
            self.logger.log('debug', f"Error in training the model: {e}")
            return
    # ________________________________________________________________________