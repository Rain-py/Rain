from Divider.DeepLearning.Tensorflow import Tensorflow
from Divider.DeepLearning.Pytorch import Pytorch

class DeepLearningFactory:
    @staticmethod
    def create_DL_interface(model, config, divider_ambassador):    
        if config["lib"] == "tensorflow":
            return Tensorflow(model, config, divider_ambassador)
        elif config["lib"] == "pytorch":
            return Pytorch(model, config, divider_ambassador)
        else:
            raise Exception("Invalid deep learning interface type")