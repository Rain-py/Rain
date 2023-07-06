import numpy as np
import dill
from Rain.Divider.MachineLearning.MachineLearningInterface import MachineLearningInterface

class LogisticRegression(MachineLearningInterface):
    def __init__(self, learning_rate=None, max_iters=None, config=None, divider_ambassador=None):
        if config is not None:
            super().__init__(config, divider_ambassador)
            self.learning_rate = config["ML"]["algorithm"]["params"]["lr"]
            self.iterations = config["iterations"]
        else:
            self.learning_rate = learning_rate
            self.iterations = max_iters
        self.weights = None
        self.bias = None
        

    def _sigmoid(self, z):
        # clip large negative values to avoid overflow
        z = np.clip(z, -500, 500)
        return 1 / (1 + np.exp(-z))
    

    def _initialize_weights(self, n_features):
        self.weights = np.random.randn(n_features)
        

    def fit(self, X, y):
        n_samples, n_features = X.shape
        self._initialize_weights(n_features)
        
        for _ in range(self.iterations):
            dw = np.zeros(n_features)
            for i in range(n_samples):
                dw += (-y[i] * X[i]) / self._sigmoid(-y[i] * X[i].dot(self.weights))

            dw = dw / n_samples

            # update weights
            self.weights = self.weights - self.learning_rate * dw    
         
            
    def predict(self, X):
        z = self._sigmoid(X.dot(self.weights))    
        y = np.where(z > 0.5, 1, 0)        
        return y
    

    def reduce_sync(self, msgs, final_iteration=False):
        n_features = msgs[0].shape[0] - 1
        
        if self.weights is None:
            self._initialize_weights(n_features)
            
        dw_sum = np.zeros(n_features)
        N = 0
        for msg in msgs:
            dw_sum += msg[:-1]
            N += msg[-1]

        dw = dw_sum / N
        self.weights -= self.learning_rate * dw
        
        if final_iteration:
            return self


    def save_model(self, iteration_num):
        data = [{"config": self.config, "model": type("LogisticRegressionModel", (object,), {"weights": self.weights})}]
        file_path = f"{self.model_base_path}{iteration_num}.pkl"
        try:
            # save the data to the file
            with open(file_path, "wb") as f:
                dill.dump(data, f)
        except Exception as e:
            self.logger.log('debug', f"Error in saving the info to the file: {e}")
            return