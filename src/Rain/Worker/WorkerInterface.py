import dill

class WorkerInterface:
    def __init__(self, id, data_base_path, iteration_num):
        self.id = id
        self.base_path = data_base_path
        self.iteration_num = iteration_num
        self.config = None
        self.epochs = None
        self.optimizer = None
        self.lib = None
        self.loss = None
        self.batch_size = None

    def receive_data(self):
        try:
            data = dill.load(open(f"{self.base_path}{self.iteration_num}.pkl", "rb"))
            return data
        except Exception as e:
            print("Error in loading the data: ", e)
            return


    def send_data(self, msg, ID):
        try:
            dill.dump(msg, open(f"{self.base_path}{ID}_{self.iteration_num}_trained.pkl", "wb"))
            print("sending data to divider")
        except Exception as e:
            print("Error in sending the data: ", e)
            return


    def run(self):
        pass