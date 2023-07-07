from Rain.Worker.WorkerPT import WorkerPT
from Rain.Worker.WorkerML import WorkerML
from Rain.Worker.WorkerTF import WorkerTF

class WorkerFactory:
    @staticmethod
    def create_worker(config):    
        if config["learning_type"] == "ML":
            return WorkerML(id=config["id"], data_base_path=config["data_base_path"], iteration_num=config["iteration_num"])
        elif config["learning_type"] == "DL":
            if config["DL"]["lib"]["type"] == "tensorflow":
                return WorkerTF(id=config["id"], data_base_path=config["data_base_path"], iteration_num=config["iteration_num"])
            elif config["DL"]["lib"]["type"] == "pytorch":
                return WorkerPT(id=config["id"], data_base_path=config["data_base_path"], iteration_num=config["iteration_num"])
            else:
                raise Exception("The library is not supported by this worker.")
            