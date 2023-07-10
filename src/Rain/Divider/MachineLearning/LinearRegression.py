import numpy as np
import dill
from Rain.Divider.MachineLearning.MachineLearningInterface import MachineLearningInterface

class LinearRegression(MachineLearningInterface):
    def __init__(self, learning_rate=None, max_iters=None, config=None, divider_ambassador=None):
        if config is not None:
            super().__init__(config, divider_ambassador)
            self.learning_rate = config["ML"]["algorithm"]["params"]["lr"]
            self.iterations = config["iterations"]
        else:
            self.learning_rate = learning_rate
            self.iterations = max_iters
        self.weights = None
    

    def _initialize_weights(self, n_features):
        self.weights = np.random.randn(n_features + 1)
        

    def fit(self, X, y):
        n_samples, n_features = X.shape
        self._initialize_weights(n_features)
        
        # prepend 1 to all the rows of X
        X = np.concatenate((np.ones((n_samples, 1)), X), axis=1)

        A = np.dot(X.T, X)
        b = np.dot(X.T, y)

        for _ in range(self.iterations):
            dw = (A + A.T).dot(self.weights) - 2 * b
            dw = dw / n_samples

            # update weights
            self.weights = self.weights - self.learning_rate * dw    
         
            
    def predict(self, X):
        n_samples = X.shape[0]
        X = np.concatenate((np.ones((n_samples, 1)), X), axis=1)
        y = np.dot(X, self.weights)
        return y
    

    def reduce_sync(self, msgs, final_iteration=False):
        n_features = msgs[0].shape[0]
        if self.weights is None:
            self._initialize_weights(n_features - 1)
            
        dw_sum = np.zeros(n_features)
        for msg in msgs:
            dw_sum += msg

        dw = dw_sum / len(msgs)
        self.weights -= self.learning_rate * dw
        
        if final_iteration:
            return self


    def save_model(self, iteration_num):
        data = [{"config": self.config, "model": type("LinearRegressionModel", (object,), {"weights": self.weights})}]
        file_path = f"{self.model_base_path}{iteration_num}.pkl"
        try:
            # save the data to the file
            with open(file_path, "wb") as f:
                dill.dump(data, f)
        except Exception as e:
            self.logger.log('error', f"Error in saving the info to the file: {e}")
            return