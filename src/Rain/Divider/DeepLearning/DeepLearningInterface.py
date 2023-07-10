import numpy as np
import dill
import threading
from abc import abstractmethod
from Rain.TemporaryFilesManager.TemporaryFilesManager import TemporaryFilesManager
from Rain.LogService.LogService import LogService

class DeepLearningInterface:
    def __init__(self, model, config, divider_ambassador):
        self.config = config
        self.lr = config["DL"]["lr"]
        self.optimizer = config["DL"]["lib"]["params"]["optimizer"]
        self.loss = config["DL"]["lib"]["params"]["loss"]
        self.iterations = config["iterations"]
        self.partitions = config["partitions"]
        self.num_of_workers = config["mode"]["params"]["num_of_workers"]
        self.model = model
        self.iteration_status = np.zeros((self.num_of_workers, self.iterations))

        self.logger = LogService("DeepLearning")
        self.divider_ambassador = divider_ambassador        

        # define the coord ip
        self.coordinator_IP = '127.0.0.1'
        
        self.model_base_path = TemporaryFilesManager.get_instance().create_temp_dir('divider/')
            

    def save_model(self, iteration_num):
        data = [{"config": self.config, "model": self.model}]
        file_path = f"{self.model_base_path}{iteration_num}.pkl"
        try:
            # save the data to the file        
            with open(file_path, "wb") as f:
                dill.dump(data, f)
        except Exception as e:
            self.logger.log('error', f"Error in saving the info to the file: {e}")
            return

    # ________________________ Synchronous Training ________________________

    def receive_gradients_sync(self, partitions, iteration_num):
        gradients = []
        try:
            for j in range(partitions):
                msg = dill.load(open(f"{self.model_base_path}{j + 1}_{iteration_num}_trained.pkl", "rb"))
                gradients.append(msg)
        except Exception as e:
            self.logger.log('error', f"Error in receiving the gradients from the workers: {e}")
            return
        return gradients
    
    
    @abstractmethod
    def reduce_gradients_sync(self, gradients):
        pass


    def worker_process_sync(self, worker_id, iteration_num, X_train_partition, y_train_partition):
        flag = False
        # handle fault tolerance
        while not flag:
            try:
                self.divider_ambassador.iteration(self.workers_ids[worker_id], self.workers_IPs[worker_id], self.workers_ports[worker_id], self.data_status[worker_id], iteration_num+1, iteration_num+1, X_train_partition, y_train_partition)
                flag = True
            except Exception as e:
                self.logger.log('error', f"Error in iteration {iteration_num} in worker {self.workers_ids[worker_id]}: {e}")
                ip, port = self.divider_ambassador.inform_coord(self.workers_IPs[worker_id], self.workers_ports[worker_id], worker_id)
                self.workers_IPs[worker_id] = ip
                self.workers_ports[worker_id] = port
                self.data_status[worker_id] = 0
                self.logger.log('error', f"Worker {worker_id + 1} is restarted on {ip}:{port} and data_status is reset to 0")

    
    def train_centralized_sync(self, X_train_partitions, y_train_partitions):
        try:  
            # get the workers info from coordinator
            self.workers_IPs, self.workers_ports, self.workers_ids = self.divider_ambassador.GetWorkersInfo(self.coordinator_IP)
            self.data_status = [0] * len(self.workers_IPs) # 0 means no data sent yet, 1 means data is already sent to the workers
        
            for i in range(self.iterations):   
                self.logger.log('info', f"Starting iteration {i + 1}/{self.iterations}")
                # Notice, the algo.py is stateless
                self.save_model(i+1) #self.partitions,
                threads = list()

                for j in range(self.partitions): # note to be considered number of workers != number of partitions
                    thread = threading.Thread(target=self.worker_process_sync, args=(j, i, X_train_partitions[j], y_train_partitions[j]))
                    # thread = threading.Thread(target=self.divider_ambassador.iteration, args=(self.workers_ids[j], self.workers_IPs[j], self.workers_ports[j], self.data_status[j], i+1, i+1, X_train_partitions[j], y_train_partitions[j]))
                    # set the data status to 1, which means the data is already sent to the worker
                    threads.append(thread)
                    thread.start()
               
                for k,thread in enumerate(threads):
                    thread.join()
                    self.data_status[k] = 1

                # self.divider_ambassador.iteration(self.coordinator_IP, i+1) # start loop
                gradients = self.receive_gradients_sync(self.partitions, i+1)
                self.reduce_gradients_sync(gradients)
                self.logger.log('info', f"Iteration {i + 1}/{self.iterations} complete.")
            return self.model
        except Exception as e:
            self.logger.log('error', f"Error in training the model: {e}")
            return

    # ________________________________________________________________________ 


    # ________________________ Asynchronous Training ________________________

    def receive_gradients_async(self, worker_id, iteration_num):
        gradients = None
        try:
            msg = dill.load(open(f"{self.model_base_path}{worker_id}_{iteration_num}_trained.pkl", "rb"))
            gradients = msg
        except Exception as e:
            self.logger.log('error', f"Error in receiving the gradients from the workers: {e}")
            return
        return gradients
    
    
    @abstractmethod
    def reduce_gradients_async(self, gradient, worker_id):
        pass


    def worker_process_async(self, worker_id, X_train_partition, y_train_partition):
        # get the workers info from coordinator
        self.workers_IPs, self.workers_ports, self.workers_ids = self.divider_ambassador.GetWorkersInfo(self.coordinator_IP)
        self.data_status = [0] * len(self.workers_IPs) # 0 means no data sent yet, 1 means data is already sent to the workers
        
        for i in range(self.iterations):
            self.logger.log('info', f"Starting iteration {i + 1}/{self.iterations}")  
            
            # fault tolerance
            # This flag is used to check if the worker completed the iteration successfully or not
            completed_iteration = False
            while not completed_iteration:
                try:
                    self.divider_ambassador.iteration(self.workers_ids[worker_id], self.workers_IPs[worker_id], self.workers_ports[worker_id], self.data_status[worker_id], i+1, self.workers_ids[worker_id], X_train_partition, y_train_partition)
                    completed_iteration = True
                except Exception as e:
                    self.logger.log('error', f"Error in iteration {i} in worker {worker_id + 1}: {e}")
                    ip, port = self.divider_ambassador.inform_coord(self.workers_IPs[worker_id], self.workers_ports[worker_id], worker_id)
                    self.workers_IPs[worker_id] = ip
                    self.workers_ports[worker_id] = port
                    self.data_status[worker_id] = 0
                    self.logger.log('error', f"Worker {worker_id + 1} is restarted on {ip}:{port} and data_status is reset to 0")

            # sending data (x_train , y_train) to workers only once
            self.data_status[worker_id] = 1

            gradient = self.receive_gradients_async(worker_id + 1, worker_id + 1)
            self.reduce_gradients_async(gradient, worker_id + 1)
            self.save_model(worker_id + 1) 
            self.logger.log('info', f"Iteration {i + 1}/{self.iterations} complete for worker {worker_id + 1}.")
        
    
    def train_centralized_async(self, X_train_partitions, y_train_partitions):
        try:
            for id in range(self.num_of_workers):
                self.save_model(id + 1)

            threads = list()
            for id in range(self.num_of_workers):
                thread = threading.Thread(target=self.worker_process_async, args=(id, X_train_partitions[id - 1], y_train_partitions[id - 1]))
                threads.append(thread)
                thread.start()
            
            # wait for all threads to finish then return the model
            for thread in threads:
                thread.join()
            
            return self.model

        except Exception as e:
            self.logger.log('error', f"Error in training the model: {e}")
            return
    # ________________________________________________________________________

    # ______________________ Semi-Asynchronous Training ______________________

    def worker_process_semi_async(self, worker_id, X_train_partition, y_train_partition):
        lock = threading.Lock()
        # get the workers info from coordinator
        self.workers_IPs, self.workers_ports, self.workers_ids = self.divider_ambassador.GetWorkersInfo(self.coordinator_IP)
        self.data_status = [0] * len(self.workers_IPs) # 0 means no data sent yet, 1 means data is already sent to the workers
        
        for i in range(self.iterations):
            self.logger.log('info', f"Starting iteration {i + 1}/{self.iterations}")  
            
            # fault tolerance
            # This flag is used to check if the worker completed the iteration successfully or not
            completed_iteration = False
            while not completed_iteration:
                try:
                    self.divider_ambassador.iteration(self.workers_ids[worker_id], self.workers_IPs[worker_id], self.workers_ports[worker_id], self.data_status[worker_id], i+1, self.workers_ids[worker_id], X_train_partition, y_train_partition)
                    completed_iteration = True
                except Exception as e:
                    self.logger.log('error', f"Error in iteration {i} in worker {worker_id + 1}: {e}")
                    ip, port = self.divider_ambassador.inform_coord(self.workers_IPs[worker_id], self.workers_ports[worker_id], worker_id)
                    self.workers_IPs[worker_id] = ip
                    self.workers_ports[worker_id] = port
                    self.data_status[worker_id] = 0
                    self.logger.log('error', f"Worker {worker_id + 1} is restarted on {ip}:{port} and data_status is reset to 0")

            # sending data (x_train , y_train) to workers only once
            self.data_status[worker_id] = 1

            gradient = self.receive_gradients_async(worker_id + 1, worker_id + 1)
            self.reduce_gradients_async(gradient, worker_id + 1)
            
            while True:
                lock.acquire()
                self.iteration_status[worker_id][i] = 1
                temp_status = self.iteration_status.copy()
                lock.release()
                in_sync_count = 0
                for j in range(len(temp_status)):
                    if j != worker_id:
                        other_worker_done_iterations = np.sum(temp_status[j])
                        if (i + 1) - other_worker_done_iterations >= self.iterations_threshold:
                            break
                        else:
                            in_sync_count += 1
                if in_sync_count == len(temp_status) - 1:
                    break
            self.save_model(worker_id + 1) 
            self.logger.log('info', f"Iteration {i + 1}/{self.iterations} complete for worker {worker_id + 1}.")


    def train_centralized_semi_async(self, X_train_partitions, y_train_partitions):
        try:
            self.iterations_threshold = self.config["iterations_threshold"]
            for id in range(self.num_of_workers):
                self.save_model(id + 1)

            threads = list()
            for id in range(self.num_of_workers):
                thread = threading.Thread(target=self.worker_process_semi_async, args=(id, X_train_partitions[id - 1], y_train_partitions[id - 1]))
                threads.append(thread)
                thread.start()
            
            # wait for all threads to finish then return the model
            for thread in threads:
                thread.join()
            
            return self.model

        except Exception as e:
            self.logger.log('error', f"Error in training the model: {e}")
            return