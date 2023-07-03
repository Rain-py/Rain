
import sys
import numpy as np
import dill
import torch
from torch.utils.data import TensorDataset, DataLoader

class TrainingWorker:
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
            print("sending data to coordinator")
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

        elif self.lib == "pytorch":
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
    
    def calculate_cluster_means(self, model, X_train):
        if model.cluster_centers is None:
            n_samples = X_train.shape[0]
            random_indices = np.random.choice(n_samples, size=model.n_clusters, replace=False)
            cluster_centers = X_train[random_indices]
        else:
            cluster_centers = model.cluster_centers

        # Assign samples to nearest cluster
        distances = self._calculate_distances(X_train, cluster_centers)
        labels = np.argmin(distances, axis=1)

        result = np.empty((model.n_clusters, cluster_centers.shape[1] + 1))
        # Update cluster centers
        for cluster in range(model.n_clusters):
            mask = labels == cluster
            if np.any(mask):
                cluster_centers[cluster] = np.mean(X_train[mask], axis=0)
            result[cluster][:-1] = cluster_centers[cluster]
            result[cluster][-1] = len(X_train[mask])
        
        return result

    def _calculate_distances(self, X, cluster_centers):
        n_clusters = cluster_centers.shape[0]
        n_samples = X.shape[0]
        distances = np.zeros((n_samples, n_clusters))

        for cluster in range(n_clusters):
            distances[:, cluster] = np.linalg.norm(X - cluster_centers[cluster], axis=1)

        return distances


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
            elif self.config["learning_type"] == "ML":
                config = self.config["ML"]
                self.algo = config["algorithm"]["type"]

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

        elif self.config["learning_type"] == "ML":
            if self.algo == "KMeans":
                # find the cluster means
                result = self.calculate_cluster_means(model, X_train)
                # Send result to the server
                self.send_data(result, self.id)


if __name__ == '__main__':
    id = sys.argv[1]
    data_base_path = sys.argv[2]
    iteration_num = sys.argv[3]
    worker = TrainingWorker(id, data_base_path, iteration_num)
    worker.run()
