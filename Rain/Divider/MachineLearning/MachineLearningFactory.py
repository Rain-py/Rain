from Rain.Divider.MachineLearning.KNN import KNN
from Rain.Divider.MachineLearning.KMeans import KMeans
from Rain.Divider.MachineLearning.NaiveBayes import NaiveBayes

class MachineLearningFactory:
    @staticmethod
    def create_ML_interface(config, divider_ambassador):
        algorithm_type = config["ML"]["algorithm"]["type"] 
        if algorithm_type == "KNN":
            # return KNN(config, divider_ambassador)
            pass
        elif algorithm_type == "KMeans":
            return KMeans(config=config, divider_ambassador=divider_ambassador)
        elif algorithm_type == "NaiveBayes":
            # return NaiveBayes(config, divider_ambassador)
            pass
        else:
            raise Exception("Invalid machine learning interface type")