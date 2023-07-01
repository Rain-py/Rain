import numpy as np
import socket
import dill
import torch
import os
import sys

from Divider.Transceiver import Transceiver

HOST = 'localhost'
PORT = 5000

class Divider:
    def __init__(self, config, model, X_train, y_train):
        self.config = config
        self.lr = self.config["lr"]
        self.optimizer = self.config["optimizer"]
        self.loss = self.config["loss"]
        self.lib = self.config["lib"]
        self.iterations = self.config["iterations"]
        self.partitions = self.config["partitions"]
        self.num_of_workers = self.config["partitions"]
        self.model = model
        # define the coord ip
        self.coordinator_IP = '127.0.0.1'
        # define the provisioner ip
        self.provisioner_IP = '127.0.0.1'
        self.transceiver = Transceiver()
        self.transceiver.create_server()
        self.data_base_path = "../../../data/"
        self.model_base_path = "../../../Divider/divider/data/"

    def send_data_to_workers(self):
        try:
            self.transceiver.send_data(self.coordinator_IP, self.provisioner_IP, self.num_of_workers, self.data_base_path)
        except Exception as e:
            print("Error in sending data to workers: ", e)
            return
        
    def send_info_to_workers(self, iteration_num):
        data = [{"config": self.config, "model": self.model}]
        file_path = f"{self.model_base_path}{iteration_num}.pkl"
        try:
            # save the data to the file        
            with open(file_path, "wb") as f:
                dill.dump(data, f)
        except Exception as e:
            print("Error in saving the info to the file: ", e)
            return

        try:
            print ("sending file: ", file_path)
            self.transceiver.send_file(self.coordinator_IP, file_path)
        except Exception as e:
            print("Error in sending the info to the workers: ", e)
            return

    # Synchronous Training    
    def receive_gradients_sync(self, partitions, iteration_num):
        gradients = []
        try:
            for j in range(partitions):
                msg = dill.load(open(f"{self.model_base_path}{j + 1}_{iteration_num}_trained.pkl", "rb"))
                gradients.append(msg)
        except Exception as e:
            print("Error in receiving the gradients from the workers: ", e)
            return
        return gradients
    
    def reduce_gradients_sync(self, gradients):
        if self.lib == "tensorflow":
            weights = self.model.get_weights() 
            # print("gradients: ", gradients)
            try:
                # Average the gradients
                gradient_avg = []
                for gradient_list_tuple in zip(*gradients):
                    gradient_avg.append(np.array([np.array(g).mean(axis=0) for g in zip(*gradient_list_tuple)]))
            except Exception as e:
                print("Error in reducing the gradients: ", e)
                return
            try:
                # Weight(new) = Weight(old) — LR * gradient loss
                weights = [weights[i] - self.lr * gradient_avg[i] for i in range(len(weights))]
                self.model.set_weights(weights)
                self.model.compile(loss=self.loss, optimizer=self.optimizer, metrics=['accuracy'])
                # print("Model summary: ", self.model.summary())
            except Exception as e:
                print("Error in calculating the new weights: ", e)
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
                print (f"Starting iteration {i + 1}/{self.iterations}")
                # Notice, the algo.py is stateless
                self.send_info_to_workers(i+1) #self.partitions,
                self.transceiver.iteration(self.coordinator_IP, i+1) # start loop
                gradients = self.receive_gradients_sync(self.partitions, i+1)
                self.reduce_gradients_sync(gradients)
                print(f"Iteration {i + 1}/{self.iterations} complete.")
            return self.model
        except Exception as e:
            print("Error in training the model: ", e)
            return


    # Asynchronous Training  
    def receive_gradients_async(self, connections):
        gradient = None
        connection = None
        while True:
            if gradient:
                break
            for j in range(len(connections)):
                data = connections[j].recv(10 * (2 ** 20))
                if data:
                    connection = connections[j]
                    gradient = dill.load(data)
                    break
        return gradient, connection
    
    def reduce_gradients_async(self, gradient):
        if self.lib == "tensorflow":
            weights = self.model.get_weights() 
            try:
                # Weight(new) = Weight(old) — LR * gradient loss
                weights = [weights[i] - self.lr * gradient[i] for i in range(len(weights))]
                self.model.set_weights(weights)
                self.model.compile(loss=self.loss, optimizer=self.optimizer, metrics=['accuracy'])
            except Exception as e:
                print("Error in calculating the new weights: ", e)
                return
                
    def train_centralized_async(self):
        connections = []
        for i in range(self.iterations):
            weights = self.model.get_weights()
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_socket.bind((HOST, PORT))
                server_socket.listen(5)

                if connections == []:
                    print("Server listening on port", PORT)
                    for j in range(self.partitions):
                        conn, addr = server_socket.accept()
                        connections.append(conn)
                        print("Connected by", addr)

                    print("All workers have connected.")
                    self.send_info_to_workers(connections)

            gradient, connection = self.receive_gradients_async(connections)
            self.send_info_to_workers([connection])

            self.reduce_gradients_async(weights, gradient)
            print(f"Iteration {i + 1}/{self.iterations} complete.")
        return self.model
    
    # destructor 
    def __del__(self):
        self.transceiver.stop_server()