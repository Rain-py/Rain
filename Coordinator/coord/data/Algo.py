import socket
import signal
import sys
import numpy as np
import dill
import multiprocessing as mp
import torch
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader

class TrainingWorker:
    def __init__(self, id, data_base_path):
        self.id = id
        self.base_path = data_base_path
        self.config = None
        self.epochs = None
        self.optimizer = None
        self.lib = None
        self.loss = None
        self.batch_size = None
        
        print("Worker", self.id, "started")

    def receive_data(self, ID):
        try:
            data = dill.load(open(f"{self.base_path}{ID}.pkl", "rb"))
            return data
        except Exception as e:
            print("Error in loading the data: ", e)
            return

    def send_data(self, msg, ID):
        try:
            dill.dump(msg, open(f"{self.base_path}{ID}_trained.pkl", "wb"))
        except Exception as e:
            print("Error in sending the data: ", e)
            return
        print("sending data to coordinator")

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


        elif self.lib == "pytorch":
            try:
                # Convert numpy arrays to PyTorch tensors
                X_train = torch.from_numpy(X_train).float()
                y_train = torch.from_numpy(y_train).long()
                # Create a TensorDataset
                train_dataset = TensorDataset(X_train, y_train)
                # Create a DataLoader for the training dataset with the defined batch size
                train_loader = DataLoader(train_dataset, batch_size=self.batch_size, shuffle=False)
                
                # TODO: Remove hardcoding
                self.optimizer = optim.Adam(model.parameters(), lr=0.001)
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
    

    def run(self):
        try:
            data = self.receive_data(self.id)[0]
        except Exception as e:
            print("Error in receiving the data: ", e)
            return

        try:
            # Configure the parameters
            self.config = data["config"]
            self.epochs = data["config"]["epochs"]
            self.optimizer = data["config"]["optimizer"]
            self.loss = data["config"]["loss"]
            self.lib = data["config"]["lib"]
            self.batch_size = data["config"]["batch_size"]
            self.lr = data["config"]["lr"]
            self.loss = data["config"]["loss"]
            model = data["model"]
        except Exception as e:
            print("Error in configuring the parameters: ", e)
            return

        # load the training data
        X_train = np.load(f"{self.base_path}/X_train_{self.id}.npy")
        y_train = np.load(f"{self.base_path}/y_train_{self.id}.npy")

        # train the model and calculate the gradient
        gradient = self.calculate_gradient(model, X_train, y_train)
        
        # Send gradient to the server
        self.send_data(gradient, self.id)


if __name__ == '__main__':
    id = sys.argv[1]
    data_base_path = "./worker/data/"
    worker = TrainingWorker(id, data_base_path)
    worker.run()
