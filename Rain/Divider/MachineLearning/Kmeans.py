import numpy as np

class KMeans:
    def __init__(self, n_clusters=8, max_iters=300):
        self.n_clusters = n_clusters
        self.max_iters = max_iters
        self.cluster_centers_ = None

    def fit(self, X):
        n_samples, n_features = X.shape

        # Initialize cluster centers randomly
        random_indices = np.random.choice(n_samples, size=self.n_clusters, replace=False)
        self.cluster_centers_ = X[random_indices]

        for _ in range(self.max_iters):
            # Assign samples to nearest cluster
            distances = self._calculate_distances(X)
            labels = np.argmin(distances, axis=1)

            # Update cluster centers
            for cluster in range(self.n_clusters):
                mask = labels == cluster
                if np.any(mask):
                    self.cluster_centers_[cluster] = np.mean(X[mask], axis=0)

    def predict(self, X):
        distances = self._calculate_distances(X)
        return np.argmin(distances, axis=1)

    def _calculate_distances(self, X):
        n_samples = X.shape[0]
        distances = np.zeros((n_samples, self.n_clusters))

        for cluster in range(self.n_clusters):
            distances[:, cluster] = np.linalg.norm(X - self.cluster_centers_[cluster], axis=1)

        return distances
