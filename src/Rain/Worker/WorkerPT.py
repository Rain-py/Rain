import numpy as np
import dill
import torch
from torch.utils.data import TensorDataset, DataLoader
from Rain.Worker.WorkerInterface import WorkerInterface

class WorkerPT(WorkerInterface):
    def __init__(self, id, data_base_path, iteration_num):
        super().__init__(id, data_base_path, iteration_num)
        


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
        if self.lib == "pytorch":
            try:
                # Convert numpy arrays to PyTorch tensors
                X_train = torch.from_numpy(X_train).float()
                y_train = torch.from_numpy(y_train).long()
                # Create a TensorDataset
                train_dataset = TensorDataset(X_train, y_train)
                # Create a DataLoader for the training dataset with the defined batch size
                train_loader = DataLoader(train_dataset, batch_size=self.batch_size, shuffle=False)
                
                old_weights = [param.clone() for param in model.parameters()]
                for epoch in range(self.epochs):
                    total_correct, total_samples, total_loss = 0, 0, 0
                    for i, (data, labels) in enumerate(train_loader):
                        # Forward pass
                        outputs = model(data)
                        loss = self.loss(outputs, labels)

                        # Backward and optimize
                        self.optimizer.zero_grad()
                        loss.backward()
                        self.optimizer.step()

                        # Compute training accuracy
                        _, predicted = torch.max(outputs.data, 1)
                        total_correct += (predicted == labels).sum().item()
                        total_samples += labels.size(0)
                        total_loss += loss.item()

                    print('Epoch [{}/{}], Loss: {:.4f}, Accuracy: {:.4f}'
                        .format(epoch+1, self.epochs, total_loss / (i + 1), total_correct / total_samples))

                new_weights = [param.clone() for param in model.parameters()]
                gradient = [(new_weights[i] - old_weights[i]) / -self.lr for i in range(len(new_weights))]
                gradient = [x.detach().numpy() for x in gradient]
                return gradient
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
            
            if self.config["learning_type"] == "DL":
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

        if self.config["learning_type"] == "DL":
            y_train = np.load(f"{self.base_path}/y_train_{self.id}.npy")
            # train the model and calculate the gradient
            gradient = self.calculate_gradient(model, X_train, y_train)
            # Send gradient to the server
            self.send_data(gradient, self.id)

        else:
            raise Exception("The learning type is not supported by this worker.")
            