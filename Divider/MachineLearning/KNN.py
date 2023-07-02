import numpy as np

class KNN():
    def __init__(self, n_neighbors=5, metric='euclidean'):
        self.K = n_neighbors
        self.metric = metric

    def __calculate_distance(self, x1, x2):
        if self.metric == 'euclidean':
            return np.sum((x1 - x2) ** 2)
        elif self.metric == 'manhattan':
            return np.sum(np.abs(x1 - x2))

    def fit(self, X_train, y_train):
        self.X_train = X_train
        self.y_train = y_train

    def predict(self, X_test):
        labels = []
        for x in X_test:
            distances = np.asarray([self.__calculate_distance(x1, x) for x1 in self.X_train])
            labels.append(np.argmax(np.bincount(np.asarray([self.y_train[x] for x in np.argsort(distances)[:self.K]]))))
            
        return np.asarray(labels)