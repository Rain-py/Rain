import numpy as np
import socket
import dill
import torch
import os
import sys
# make path in the file directory accessible

sys.path.append('../../Divider')
from Div_transmitter import div_transmitter
sys.path.pop()


HOST = 'localhost'
PORT = 5000


class Divider:
    def __init__(self, config, model, X_train, y_train):
        self.config = config
        self.model = model
        # define the coord ip
        self.coordinator_IP = '127.0.0.1'
        # define the provisioner ip
        self.provisioner_IP = '127.0.0.1'

        self.transmitter = div_transmitter()
        self.transmitter.create_server()

    def send_data_to_workers(self):
        path = "../../data/"
        self.transmitter.send_data(self.coordinator_IP, self.provisioner_IP, 1, path) # self.config["partitions"]
        
    def send_info_to_workers(self, connections):
        path = "../../data/"
        print("sending info to workers")
        for j in range(connections):
            data = [{"config": self.config, "model": self.model}]
            
            file_path = f"{path}{j + 1}.pkl"
            # save the data to the file        
            with open(file_path, "wb") as f:
                dill.dump(data, f)

            print ("sending file: ", file_path)
            self.transmitter.send_file(self.coordinator_IP, file_path) # self.config["partitions"]
        
    def receive_sync(self, connections):
        gradients = []
        for j in range(connections):
            msg = dill.load(open(f"../../Divider/divider/data/{j + 1}_trained.pkl", "rb"))
            gradients.append(msg)
        return gradients
    

    def reduce_gradients_sync(self, gradients):
        if self.config["lib"] == "tensorflow":
            weights = self.model.get_weights() 
            print("gradients: ", gradients)
            # Average the gradients
            gradient_avg = []
            for gradient_list_tuple in zip(*gradients):
                gradient_avg.append(np.array([np.array(g).mean(axis=0) for g in zip(*gradient_list_tuple)]))
        
            # Weight(new) = Weight(old) — LR * gradient loss
            weights = [weights[i] - self.config["lr"] * gradient_avg[i] for i in range(len(weights))]
            self.model.set_weights(weights)
            self.model.compile(loss=self.config["loss"], optimizer=self.config["optimizer"], metrics=['accuracy'])
        
        elif self.config["lib"] == "pytorch":  
            weights = [param.clone().detach().numpy() for param in self.model.parameters()]  
            # Average the gradients
            gradient_avg = []
            for gradient_list_tuple in zip(*gradients):
                gradient_avg.append(np.array([np.array(g).mean(axis=0) for g in zip(*gradient_list_tuple)]))

            # Weight(new) = Weight(old) — LR * gradient loss
            weights = [weights[i] - self.config["lr"] * gradient_avg[i] for i in range(len(weights))]
            
            state_dict = self.model.state_dict()
            for key, value in zip(state_dict.keys(), weights):
                state_dict[key] = torch.from_numpy(value)

            self.model.load_state_dict(state_dict)


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
    

    def reduce_gradients_async(self, weights, gradient, lib):
        if lib == "tensorflow":
            # Weight(new) = Weight(old) — LR * gradient loss
            weights = [weights[i] - self.config["lr"] * gradient[i] for i in range(len(weights))]
            self.model.set_weights(weights)
            self.model.compile(loss=self.config["loss"], optimizer=self.config["optimizer"], metrics=['accuracy'])
                

    def train_centralized_sync(self):
        for i in range(self.config["iterations"]):       
            # Notice, the algo.py is stateless
            self.send_info_to_workers(self.config["partitions"])
            self.transmitter.iteration(self.coordinator_IP) # start loop
            gradients = self.receive_sync(self.config["partitions"])
            self.reduce_gradients_sync(gradients)
            print(f"Iteration {i + 1}/{self.config['iterations']} complete.")

        return self.model


    def train_centralized_async(self):
        connections = []
        for i in range(self.config["iterations"]):
            weights = self.model.get_weights()
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_socket.bind((HOST, PORT))
                server_socket.listen(5)

                if connections == []:
                    print("Server listening on port", PORT)
                    for j in range(self.config["partitions"]):
                        conn, addr = server_socket.accept()
                        connections.append(conn)
                        print("Connected by", addr)

                    print("All workers have connected.")
                    self.send_info_to_workers(connections)

            gradient, connection = self.receive_gradients_async(connections)
            self.send_info_to_workers([connection])

            self.reduce_gradients_async(weights, gradient)
            print(f"Iteration {i + 1}/{self.config['iterations']} complete.")

        # self.send_info_to_workers(connections, "stop")
        return self.model
    
    # destractor 
    def __del__(self):
        self.transmitter.stop_server()