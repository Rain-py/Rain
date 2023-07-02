import numpy as np
import socket
import dill
import torch
import threading

from Divider.DividerAmbassador import DividerAmbassador
import os
import sys
sys.path.append('../LogService')
from LogService.LogService import LogService
sys.path.pop()
HOST = 'localhost'
PORT = 5000

class Divider:
    def __init__(self, config, model):
        self.config = config
        self.lr = self.config["lr"]
        self.optimizer = self.config["optimizer"]
        self.loss = self.config["loss"]
        self.lib = self.config["lib"]
        self.iterations = self.config["iterations"]
        self.partitions = self.config["partitions"]
        self.num_of_workers = self.config["partitions"]
        self.model = model
        self.logger = LogService("Divider")

        # define workers info 
        self.worker_IPs = ['127.0.0.1', '127.0.0.1', '127.0.0.1'] 
        self.worker_ports =[50151, 50152, 50153]
        self.worker_ids =  [1, 2, 3]
        self.data_status = [0] * len(self.worker_IPs) # 0 means no data sent yet, 1 means data is already sent to the workers

        # define the coord ip
        self.coordinator_IP = '127.0.0.1'
        # define the provisioner ip
        self.provisioner_IP = '127.0.0.1'
        self.divider_ambassador = DividerAmbassador()
        self.data_base_path = "../../../data/"
        self.model_base_path = "../../../Divider/divider/data/"
        if not os.path.exists(self.model_base_path):
            os.makedirs(self.model_base_path) 

    def serve(self):
        self.divider_ambassador.serve()
    def stop_serving(self):
        self.divider_ambassador.stop_serving()
        self.logger.log('debug', f"Divider stopped serving")
    
    def send_data_to_workers(self):
        try:
            self.divider_ambassador.send_data(self.coordinator_IP, self.provisioner_IP, self.num_of_workers, self.data_base_path)
        except Exception as e:
            self.logger.log('debug', f"Error in sending data to workers: {e}")
            return
        
    def send_info_to_workers(self, iteration_num):
        data = [{"config": self.config, "model": self.model}]
        file_path = f"{self.model_base_path}{iteration_num}.pkl"
        try:
            # save the data to the file        
            with open(file_path, "wb") as f:
                dill.dump(data, f)
        except Exception as e:
            self.logger.log('debug', f"Error in saving the info to the file: {e}")
            return

        try:
            self.logger.log('debug', f"Sending file: {file_path}")
            self.divider_ambassador.send_file(self.coordinator_IP, file_path)
        except Exception as e:
            self.logger.log('debug', f"Error in sending the info to the workers: {e}")
            return

    # Synchronous Training    
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
    
    def reduce_gradients_sync(self, gradients):
        if self.lib == "tensorflow":
            weights = self.model.get_weights() 
            try:
                # Average the gradients
                gradient_avg = []
                for gradient_list_tuple in zip(*gradients):
                    gradient_avg.append(np.array([np.array(g).mean(axis=0) for g in zip(*gradient_list_tuple)]))
            except Exception as e:
                self.logger.log('debug', f"Error in reducing the gradients: {e}")
                return
            try:
                # Weight(new) = Weight(old) — LR * gradient loss
                weights = [weights[i] - self.lr * gradient_avg[i] for i in range(len(weights))]
                self.model.set_weights(weights)
                self.model.compile(loss=self.loss, optimizer=self.optimizer, metrics=['accuracy'])
            except Exception as e:
                self.logger.log('debug', f"Error in calculating the new weights: {e}")
                return
        
        elif self.lib == "pytorch":  
            weights = [param.clone().detach().numpy() for param in self.model.parameters()]  
            # Average the gradients
            gradient_avg = []
            for gradient_list_tuple in zip(*gradients):
                gradient_avg.append(np.array([np.array(g).mean(axis=0) for g in zip(*gradient_list_tuple)]))

            # Weight(new) = Weight(old) — LR * gradient loss
            weights = [weights[i] - self.lr * gradient_avg[i] for i in range(len(weights))]
            
            state_dict = self.model.state_dict()
            for key, value in zip(state_dict.keys(), weights):
                state_dict[key] = torch.from_numpy(value)

            self.model.load_state_dict(state_dict)

    def train_centralized_sync(self):
        try:  
            for i in range(self.iterations):   
                self.logger.log('debug', f"Starting iteration {i + 1}/{self.iterations}")
                # Notice, the algo.py is stateless
                self.send_info_to_workers(i+1) #self.partitions,
                self.divider_ambassador.iteration(self.coordinator_IP, i+1) # start loop
                gradients = self.receive_gradients_sync(self.partitions, i+1)
                self.reduce_gradients_sync(gradients)
                self.logger.log('debug', f"Iteration {i + 1}/{self.iterations} complete.")
            return self.model
        except Exception as e:
            self.logger.log('debug', f"Error in training the model: {e}")
            return


    # Asynchronous Training  
    def receive_gradients_async(self, worker_id, iteration_num):
        gradients = None
        try:
            msg = dill.load(open(f"{self.model_base_path}{worker_id}_{iteration_num}_trained.pkl", "rb"))
            gradients = msg
        except Exception as e:
            print("Error in receiving the gradients from the workers: ", e)
            return
        return gradients
    
    def reduce_gradients_async(self, worker_id, gradient):
        if self.lib == "tensorflow":
            weights = self.model.get_weights() 
            weights = [weights[i] - (self.lr / self.partitions) * gradient[i] for i in range(len(weights))]
            self.model.set_weights(weights)
            self.model.compile(loss=self.loss, optimizer=self.optimizer, metrics=['accuracy'])
            self.logger.log('debug', f"update is done by worker {worker_id}")

    def worker_process_async(self, worker_id):
        for i in range(self.iterations):
            self.logger.log('debug', f"Starting iteration {i + 1}/{self.iterations}")   
            self.divider_ambassador.iteration_async(self.worker_ids[worker_id], self.worker_IPs[worker_id], self.worker_ports[worker_id], self.data_status[worker_id], i+1)
            if i == 1: # sending data (x_train , y_train) to workers only once
                self.data_status[worker_id] = 1

            gradient = self.receive_gradients_async(worker_id + 1,worker_id + 1) # worker_id, worker_id
            self.reduce_gradients_async(worker_id + 1, gradient)
            self.send_info_to_workers(worker_id + 1) 
            self.logger.log('debug', f"Iteration {i + 1}/{self.iterations} complete for worker {worker_id + 1}.")
        
    def train_centralized_async(self):
        try:
            for id in range(self.num_of_workers):
                self.send_info_to_workers(id + 1)

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
    
    # destructor 
    def __del__(self):
        self.divider_ambassador.stop_serving()