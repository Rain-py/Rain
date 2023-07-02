from Divider.MachineLearning.KNN_classifier import KNN


class DeepLearningFactory:
    @staticmethod
    def create_DL_interface(config, divider_ambassador):    
        if config["algo"] == "knn":
            return KNN(config, divider_ambassador)
        else:
            raise Exception("Invalid deep learning interface type")