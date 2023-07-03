from Rain.Divider.DeepLearning.Tensorflow import Tensorflow
from Rain.Divider.DeepLearning.Pytorch import Pytorch

class DeepLearningFactory:
    @staticmethod
    def create_DL_interface(model, config, divider_ambassador):    
        if config["DL"]["lib"] == "tensorflow":
            return Tensorflow(model, config, divider_ambassador)
        elif config["DL"]["lib"] == "pytorch":
            return Pytorch(model, config, divider_ambassador)
        else:
            raise Exception("Invalid deep learning interface type")