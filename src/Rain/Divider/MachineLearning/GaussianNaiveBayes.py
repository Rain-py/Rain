import numpy as np
import dill
from Rain.Divider.MachineLearning.MachineLearningInterface import MachineLearningInterface

class GaussianNaiveBayes(MachineLearningInterface):
    def __init__(self, config=None, divider_ambassador=None):
        if config is not None:
            super().__init__(config, divider_ambassador)
            self.iterations = 1
        self.classes = None
        self.class_priors = None
        self.class_likelihoods = None

    def fit(self, X, y):
        self.classes = np.unique(y)
        self.num_classes = len(self.classes)
        self.class_priors = self.__calculate_class_priors(y)
        self.class_likelihoods = self.__calculate_class_likelihoods(X, y)

    def __calculate_class_priors(self, y):
        class_counts = np.bincount(y)
        total_samples = y.shape[0]
        return class_counts / total_samples

    def __calculate_class_likelihoods(self, X, y):
        num_features = X.shape[1]
        class_likelihoods = []

        for class_label in self.classes:
            class_samples = X[y == class_label]
            feature_likelihoods = []

            for feature_idx in range(num_features):
                feature_values = class_samples[:, feature_idx]
                feature_likelihood = self.__calculate_feature_likelihood(feature_values)
                feature_likelihoods.append(feature_likelihood)

            class_likelihoods.append(feature_likelihoods)

        return np.array(class_likelihoods)

    def __calculate_feature_likelihood(self, feature_values):
        feature_likelihood = {
            "mean": np.mean(feature_values),
            "std": np.std(feature_values),
        }
        return feature_likelihood

    def predict(self, X):
        num_samples = X.shape[0]
        predictions = np.zeros(num_samples, dtype=int)

        for i in range(num_samples):
            sample = X[i]
            posterior_probs = []

            for class_idx in range(self.num_classes):
                class_prior = self.class_priors[class_idx]
                class_likelihoods = self.class_likelihoods[class_idx]
                class_posterior = class_prior

                for feature_idx, feature_value in enumerate(sample):
                    feature_likelihood = class_likelihoods[feature_idx]
                    class_posterior *= self.__calculate_gaussian_probability(
                        feature_value, feature_likelihood['mean'], feature_likelihood['std']
                    )

                posterior_probs.append(class_posterior)

            predicted_class = np.argmax(posterior_probs)
            predictions[i] = predicted_class

        return predictions


    def __calculate_gaussian_probability(self, x, mean, std):
        exponent = np.exp(-((x - mean) ** 2) / (2 * (std ** 2)))
        probability = (1 / (np.sqrt(2 * np.pi) * std)) * exponent
        return probability
    

    def reduce_sync(self, msgs, final_iteration=False):
        self.num_classes = len(msgs[0]["class_likelihoods"])
        num_features = len(msgs[0]["class_likelihoods"][0])
        total_samples = 0
        class_counts = {}
        for msg in msgs:
            total_samples += msg["samples_count"]
            for class_label in msg["class_counts"]:
                if class_label not in class_counts:
                    class_counts[class_label] = msg["class_counts"][class_label]
                else:
                    class_counts[class_label] += msg["class_counts"][class_label]
        class_counts = dict(sorted(class_counts.items()))
        self.class_priors = np.asarray(list(class_counts.values())) / total_samples

        
        self.class_likelihoods = []
        for _ in range(self.num_classes):
            feature_likelihoods = []

            for _ in range(num_features):
                feature_likelihood = {
                    "mean": 0,
                    "std": 0
                }
                feature_likelihoods.append(feature_likelihood)

            self.class_likelihoods.append(feature_likelihoods)
        self.class_likelihoods = np.asarray(self.class_likelihoods)

        n = np.zeros((self.num_classes, num_features))
        for i in range(self.num_classes):
            for j in range(num_features):
                for msg in msgs:
                    self.class_likelihoods[i][j]["mean"] += msg["class_likelihoods"][i][j]["sum"]
                    self.class_likelihoods[i][j]["std"] += msg["class_likelihoods"][i][j]["squared_sum"]
                    n[i][j] += msg["class_likelihoods"][i][j]["n"]
        
        for i in range(self.num_classes):
            for j in range(num_features):
                self.class_likelihoods[i][j]["mean"] /= n[i][j]
                self.class_likelihoods[i][j]["std"] /= n[i][j]
                self.class_likelihoods[i][j]["std"] = np.sqrt(self.class_likelihoods[i][j]["std"] - np.square(self.class_likelihoods[i][j]["mean"]))
        return self


    def save_model(self, iteration_num):
        data = [{"config": self.config, "model": None}]
        file_path = f"{self.model_base_path}{iteration_num}.pkl"
        try:
            # save the data to the file
            with open(file_path, "wb") as f:
                dill.dump(data, f)
        except Exception as e:
            self.logger.log('debug', f"Error in saving the info to the file: {e}")
            return