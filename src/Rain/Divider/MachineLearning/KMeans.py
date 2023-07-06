import numpy as np
import dill
from Rain.Divider.MachineLearning.MachineLearningInterface import MachineLearningInterface

class KMeans(MachineLearningInterface):
    def __init__(self, n_clusters=None, max_iters=None, config=None, divider_ambassador=None):
        if config is not None:
            super().__init__(config, divider_ambassador)
            self.n_clusters = config["ML"]["algorithm"]["params"]["K"]
            self.iterations = config["iterations"]
        else:
            self.n_clusters = n_clusters
            self.iterations = max_iters
        self.cluster_centers = None

    def fit(self, X):
        n_samples = X.shape[0]
        # Initialize cluster centers randomly
        random_indices = np.random.choice(n_samples, size=self.n_clusters, replace=False)
        self.cluster_centers = X[random_indices]

        old_labels = None
        for i in range(self.iterations):
            # Assign samples to nearest cluster
            distances = self._calculate_distances(X)
            labels = np.argmin(distances, axis=1)
            
            if old_labels is not None and np.all(old_labels == labels):
                print(f"Converged at iteration {i}")
                return labels

            # Update cluster centers
            for cluster in range(self.n_clusters):
                mask = labels == cluster
                if np.any(mask):
                    self.cluster_centers[cluster] = np.mean(X[mask], axis=0)

            old_labels = labels
        
        return labels


    def _calculate_distances(self, X):
        n_samples = X.shape[0]
        distances = np.zeros((n_samples, self.n_clusters))

        for cluster in range(self.n_clusters):
            distances[:, cluster] = np.linalg.norm(X - self.cluster_centers[cluster], axis=1)

        return distances


    def reduce_sync(self, msgs, final_iteration=False):
        features_count = msgs[0].shape[1] - 1
        if self.cluster_centers is None:
            self.cluster_centers = np.zeros((self.n_clusters, features_count))
        cluster_sums = np.zeros((self.n_clusters, features_count))
        cluster_counts = np.zeros(self.n_clusters)
        
        for msg in msgs:
            for cluster in range(self.n_clusters):
                cluster_sums[cluster] += msg[cluster][:-1] * msg[cluster][-1]
                cluster_counts[cluster] += msg[cluster][-1]
        for cluster in range(self.n_clusters):
            self.cluster_centers[cluster] = cluster_sums[cluster] / cluster_counts[cluster]
        
        if final_iteration:
            return self
        
    def get_labels(self, X):
        distances = self._calculate_distances(X)
        labels = np.argmin(distances, axis=1)
        return labels


    def save_model(self, iteration_num):
        data = [{"config": self.config, "model": type("KMeansModel", (object,), {"cluster_centers": self.cluster_centers, "n_clusters": self.n_clusters})}]
        file_path = f"{self.model_base_path}{iteration_num}.pkl"
        try:
            # save the data to the file
            with open(file_path, "wb") as f:
                dill.dump(data, f)
        except Exception as e:
            self.logger.log('debug', f"Error in saving the info to the file: {e}")
            return