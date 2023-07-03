import numpy as np


class NaiveBayes:
    def __init__(self):
        self.classes = None
        self.class_priors = None
        self.class_likelihoods = None

    def fit(self, X, y):
        self.classes = np.unique(y)
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
            'mean': np.mean(feature_values),
            'std': np.std(feature_values),
        }
        return feature_likelihood

    def predict(self, X):
        num_samples = X.shape[0]
        num_classes = len(self.classes)
        predictions = np.zeros(num_samples, dtype=int)

        for i in range(num_samples):
            sample = X[i]
            posterior_probs = []

            for class_idx in range(num_classes):
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
            predictions[i] = self.classes[predicted_class]

        return predictions

    def __calculate_gaussian_probability(self, x, mean, std):
        exponent = np.exp(-((x - mean) ** 2) / (2 * (std ** 2)))
        probability = (1 / (np.sqrt(2 * np.pi) * std)) * exponent
        return probability
