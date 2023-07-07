class WorkerFactory:
    @staticmethod
    def create_worker(setup, worker_id, data_base_path, iteration_num):  
        try:  
            if setup == "ML":
                from Rain.Worker.WorkerML import WorkerML
                return WorkerML(worker_id, data_base_path, iteration_num)
            elif setup == "TF":
                from Rain.Worker.WorkerTF import WorkerTF
                return WorkerTF(worker_id, data_base_path, iteration_num)
            elif setup == "PT":
                from Rain.Worker.WorkerPT import WorkerPT
                return WorkerPT(worker_id, data_base_path, iteration_num)
            else:
                raise Exception(f"The setup: {setup} is not supported by this worker.")
        except Exception as e:
            raise Exception(f"Error creating the worker: {e}")
            