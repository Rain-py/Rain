import numpy as np
import dill
from Rain.Worker.WorkerInterface import WorkerInterface

class WorkerML(WorkerInterface):
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
    
    def calculate_probabilities(self, X_train, y_train):
        result = {
            "class_counts": {},
            "class_likelihoods": None,
            "samples_count": len(y_train)
        }
        count = np.bincount(y_train)
        for i in range(len(count)):
            result["class_counts"][i] = count[i]

        result["class_likelihoods"] = self.calculate_class_likelihoods(X_train, y_train)
        return result
    
    def calculate_class_likelihoods(self, X, y):
        num_features = X.shape[1]
        class_likelihoods = []
        classes = np.unique(y)

        for class_label in classes:
            class_samples = X[y == class_label]
            feature_likelihoods = []

            for feature_idx in range(num_features):
                feature_values = class_samples[:, feature_idx]
                feature_likelihood = self.calculate_feature_likelihood(feature_values)
                feature_likelihoods.append(feature_likelihood)

            class_likelihoods.append(feature_likelihoods)
        return np.asarray(class_likelihoods)

    def calculate_feature_likelihood(self, feature_values):
        feature_likelihood = {
            'sum': np.sum(feature_values),
            'squared_sum': np.sum(np.square(feature_values)),
            'n': feature_values.shape[0]
        }
        return feature_likelihood
    
    def sigmoid(self, z):
        # clip large negative values to avoid overflow
        z = np.clip(z, -500, 500)
        return 1 / (1 + np.exp(-z))
    
    def calculate_logistic_regression_gradient(self, model, X, y):
        n_samples, n_features = X.shape
        
        if model.weights is None:
            weights = np.random.randn(n_features)
        else:
            weights = model.weights

        dw = np.zeros(n_features)
        for i in range(n_samples):
            dw += (-y[i] * X[i]) / self.sigmoid(-y[i] * X[i].dot(weights))

        result = np.empty(n_features + 1)
        result[:-1] = dw
        result[-1] = n_samples
        return result
    
    def calculate_linear_regression_gradient(self, model, X, y):
        n_samples, n_features = X.shape
        if model.weights is None:
            weights = np.random.randn(n_features + 1)
        else:
            weights = model.weights

        # prepend 1 to all the rows of X
        X = np.concatenate((np.ones((n_samples, 1)), X), axis=1)

        A = np.dot(X.T, X)
        b = np.dot(X.T, y)

        dw = (A + A.T).dot(weights) - 2 * b
        dw = dw / n_samples
        return dw


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
            
            if self.config["learning_type"] == "ML":
                config = self.config["ML"]
                self.algo = config["algorithm"]["type"]
            else:
                raise Exception("Learning type is not supported")

        except Exception as e:
            print("Error in configuring the parameters: ", e)
            return

        # load the training data
        X_train = np.load(f"{self.base_path}/X_train_{self.id}.npy")
        y_train = np.load(f"{self.base_path}/y_train_{self.id}.npy")

        if self.config["learning_type"] == "ML":
            if self.algo == "KMeans":
                # find the cluster means
                result = self.calculate_cluster_means(model, X_train)
                # Send result to the server
                self.send_data(result, self.id)
            elif self.algo == "GaussianNaiveBayes":
                result = self.calculate_probabilities(X_train, y_train)
                self.send_data(result, self.id)
            elif self.algo == "LogisticRegression":
                result = self.calculate_logistic_regression_gradient(model, X_train, y_train)
                self.send_data(result, self.id)
            elif self.algo == "LinearRegression":
                result = self.calculate_linear_regression_gradient(model, X_train, y_train)
                self.send_data(result, self.id)
            else:
                raise Exception("Algorithm is not supported")
        else:
            raise Exception("Learning type is not supported")