from Rain.Divider.MachineLearning.KMeans import KMeans
from Rain.Divider.MachineLearning.GaussianNaiveBayes import GaussianNaiveBayes
from Rain.Divider.MachineLearning.LogisticRegression import LogisticRegression
from Rain.Divider.MachineLearning.LinearRegression import LinearRegression
from Rain.Divider.MachineLearning.KNN import KNN

class MachineLearningFactory:
    @staticmethod
    def create_ML_interface(config, divider_ambassador):
        algorithm_type = config["ML"]["algorithm"]["type"] 
        if algorithm_type == "KMeans":
            return KMeans(config=config, divider_ambassador=divider_ambassador)
        elif algorithm_type == "GaussianNaiveBayes":
            return GaussianNaiveBayes(config=config, divider_ambassador=divider_ambassador)
        elif algorithm_type == "LogisticRegression":
            return LogisticRegression(config=config, divider_ambassador=divider_ambassador)
        elif algorithm_type == "LinearRegression":
            return LinearRegression(config=config, divider_ambassador=divider_ambassador)
        elif algorithm_type == "KNN":
            return KNN(config, divider_ambassador)
        else:
            raise Exception("Invalid machine learning interface type")