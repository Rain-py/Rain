from Rain.Divider.MachineLearning.KNN import KNN


class DeepLearningFactory:
    @staticmethod
    def create_DL_interface(config, divider_ambassador):    
        if config["ML"]["algorithm"]["type"] == "KNN":
            return KNN(config, divider_ambassador)
        else:
            raise Exception("Invalid deep learning interface type")