from Rain.Worker.WorkerPT import WorkerPT
from Rain.Worker.WorkerML import WorkerML
from Rain.Worker.WorkerTF import WorkerTF

class WorkerFactory:
    @staticmethod
    def create_worker(setup, worker_id, data_base_path, iteration_num):    
        if setup == "ML":
            return WorkerML(worker_id, data_base_path, iteration_num)
        elif setup == "TF":
            return WorkerTF(worker_id, data_base_path, iteration_num)
        elif setup == "PT":
            return WorkerPT(worker_id, data_base_path, iteration_num)
        else:
            raise Exception(f"The setup: {setup} is not supported by this worker.")
            