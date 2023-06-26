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
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.path = "./worker/data/"

    def receive_data(self, ID):
        data = dill.load(open(f"{self.path}{ID}.pkl", "rb"))
        return data

    def send_data(self, msg, ID):
        print("saving data ..")
        dill.dump(msg, open(f"{self.path}{ID}_trained.pkl", "wb"))

    def calculate_gradient(self, model, X_train, y_train, config):
        if config["lib"] == "tensorflow":
            old_weights = model.get_weights()
            model.compile(loss=config["loss"], optimizer=config["optimizer"], metrics=['accuracy'])
            model.fit(X_train, y_train, epochs=config["epochs"], batch_size=config["batch_size"])
            new_weights = model.get_weights()
            gradients = [(new_weights[i] - old_weights[i]) / -config["lr"] for i in range(len(new_weights))]
            return gradients


        elif config["lib"] == "pytorch":
            # Convert numpy arrays to PyTorch tensors
            X_train = torch.from_numpy(X_train).float()
            y_train = torch.from_numpy(y_train).long()

            # Create a TensorDataset
            train_dataset = TensorDataset(X_train, y_train)

            # TODO: Remove hardcoding
            config["optimizer"] = optim.Adam(model.parameters(), lr=0.001)

            # Create a DataLoader for the training dataset with the defined batch size
            train_loader = DataLoader(train_dataset, batch_size=config["batch_size"], shuffle=False)
            
            old_weights = [param.clone() for param in model.parameters()]
            for epoch in range(config["epochs"]):
                total_correct = 0
                total_samples = 0
                total_loss = 0
                
                for i, (data, labels) in enumerate(train_loader):
                    # Forward pass
                    outputs = model(data)
                    loss = config["loss"](outputs, labels)

                    # Backward and optimize
                    config["optimizer"].zero_grad()
                    loss.backward()
                    config["optimizer"].step()

                    # Compute training accuracy
                    _, predicted = torch.max(outputs.data, 1)
                    total_correct += (predicted == labels).sum().item()
                    total_samples += labels.size(0)
                    total_loss += loss.item()

                # Print loss and accuracy at the end of the epoch
                epoch_loss = total_loss / (i + 1)
                epoch_accuracy = total_correct / total_samples
                print('Epoch [{}/{}], Loss: {:.4f}, Accuracy: {:.4f}'
                    .format(epoch+1, config["epochs"], epoch_loss, epoch_accuracy))

            new_weights = [param.clone() for param in model.parameters()]
            gradient = [(new_weights[i] - old_weights[i]) / -config["lr"] for i in range(len(new_weights))]
            gradient = [x.detach().numpy() for x in gradient]
            return gradient
    

    def run(self):
        X_train = None
        y_train = None
        config = None
        ID = sys.argv[1]
        print("Worker", ID, "started")
        # while True:
        data = self.receive_data(ID)
        print(data)
        if data[0] == "initial":
            data = data[1]
            ID = data["ID"]
            config = data["config"]
            X_train = np.load(f"{self.path}/X_train_{ID}.npy")
            y_train = np.load(f"{self.path}/y_train_{ID}.npy")
            self.send_data("ready", ID)
        elif data[0] == "train":
            model = data[1]
            gradient = self.calculate_gradient(model, X_train, y_train, config)
            # Send gradient to the server
            self.send_data(gradient, ID)



if __name__ == '__main__':

    host = 'localhost'
    port = 5000
    worker = TrainingWorker(host, port)
    worker.run()


# if __name__ == '__main__':
#     worker_id = sys.argv[1]
#     X_train = np.load(f'worker/X_train/X_train_{worker_id}.npy')
#     y_train = np.load(f'worker/Y_train/Y_train_{worker_id}.npy')
#     model = train_model(X_train, y_train)
#     model.save(f'worker/model_{worker_id}.h5')