import numpy as np
import dill
from Rain.Worker.WorkerInterface import WorkerInterface

class WorkerTF(WorkerInterface):
    def __init__(self, id, data_base_path, iteration_num):
        super().__init__(id, data_base_path, iteration_num)
        self.algo = None


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


    def calculate_gradient(self, model, X_train, y_train):
        if self.lib == "tensorflow":
            try:
                old_weights = model.get_weights()
                model.compile(loss=self.loss, optimizer=self.optimizer, metrics=['accuracy'])
                model.fit(X_train, y_train, epochs=self.epochs, batch_size=self.batch_size)
                new_weights = model.get_weights()
                gradients = [(new_weights[i] - old_weights[i]) / -self.lr for i in range(len(new_weights))]
                return gradients
            except Exception as e:
                print("Error in calculating the gradient: ", e)
                return
        else:
            raise Exception("The library is not supported by this worker.")

    def run(self):
        try:
            data = self.receive_data()[0]
        except Exception as e:
            print("Error in receiving the data: ", e)
            return

        try:
            # Configure the parameters
            self.config = data["config"]
            model = data["model"]
            
            if self.config["learning_type"] == "DL" and self.config["DL"]["lib"]["type"] == "tensorflow":
                config = self.config["DL"]
                self.lib = config["lib"]["type"]
                self.optimizer = config["lib"]["params"]["optimizer"]
                self.loss = config["lib"]["params"]["loss"]
                self.epochs = config["epochs"]
                self.batch_size = config["batch_size"]
                self.lr = config["lr"]
            else:
                raise Exception("The learning type is not supported by this worker.")

        except Exception as e:
            print("Error in configuring the parameters: ", e)
            return

        # load the training data
        X_train = np.load(f"{self.base_path}/X_train_{self.id}.npy")

        if self.config["learning_type"] == "DL" and self.config["DL"]["lib"]["type"] == "tensorflow":
            y_train = np.load(f"{self.base_path}/y_train_{self.id}.npy")
            # train the model and calculate the gradient
            gradient = self.calculate_gradient(model, X_train, y_train)
            # Send gradient to the server
            self.send_data(gradient, self.id)

        else:
            raise Exception("The learning type is not supported by this worker.")
            