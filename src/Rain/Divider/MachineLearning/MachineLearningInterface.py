import dill
import threading
from abc import abstractmethod
from Rain.TemporaryFilesManager.TemporaryFilesManager import TemporaryFilesManager
from Rain.LogService.LogService import LogService

class MachineLearningInterface:
    def __init__(self, config, divider_ambassador):
        self.config = config
        self.partitions = config["partitions"]
        self.num_of_workers = config["mode"]["params"]["num_of_workers"]

        self.logger = LogService("MachineLearning")
        self.divider_ambassador = divider_ambassador        

        # define the coord ip
        self.coordinator_IP = '127.0.0.1'
        
        self.model_base_path = TemporaryFilesManager.get_instance().create_temp_dir('divider/')


    @abstractmethod
    def save_model(self, iteration_num):
        pass


    def receive_sync(self, iteration_num):
        msgs = []
        try:
            for j in range(self.partitions):
                msg = dill.load(open(f"{self.model_base_path}{j + 1}_{iteration_num}_trained.pkl", "rb"))
                msgs.append(msg)
        except Exception as e:
            self.logger.log('error', f"Error in receiving from the workers: {e}")
            return
        return msgs
    
    
    @abstractmethod
    def reduce_sync(self, msgs, final_iteration=False):
        pass


    def train_centralized_sync(self, X_train_partitions, y_train_partitions):
        try:  
            # get the workers info from coordinator
            self.workers_IPs, self.workers_ports, self.workers_ids = self.divider_ambassador.GetWorkersInfo(self.coordinator_IP)
            self.data_status = [0] * len(self.workers_IPs) # 0 means no data sent yet, 1 means data is already sent to the workers
        
            for i in range(self.iterations):   
                self.logger.log('info', f"Starting iteration {i + 1}/{self.iterations}")
                # Notice, the algo.py is stateless
                self.save_model(i + 1)
                threads = list()
                for j in range(self.partitions): # note to be considered number of workers != number of partitions
                    thread = threading.Thread(target=self.divider_ambassador.iteration, args=(self.workers_ids[j], self.workers_IPs[j], self.workers_ports[j], self.data_status[j], i+1, i+1, X_train_partitions[j], y_train_partitions[j]))
                    if i == 0:
                        self.data_status[j] = 1
                    threads.append(thread)
                    thread.start()
                for thread in threads:
                    thread.join()
                # self.divider_ambassador.iteration(self.coordinator_IP, i+1) # start loop
                msgs = self.receive_sync(i + 1)
                model = self.reduce_sync(msgs, final_iteration=(i == self.iterations - 1))
                self.logger.log('info', f"Iteration {i + 1}/{self.iterations} complete.")
            return model
        except Exception as e:
            self.logger.log('error', f"Error in training the model: {e}")
            return