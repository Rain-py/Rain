from Divider.DeepLearning.Tensorflow import Tensorflow
from Divider.DeepLearning.Pytorch import Pytorch

class DeepLearningFactory:
    @staticmethod
    def create_DL_interface(model, config, logger):    
        if config["lib"] == "tensorflow":
            return Tensorflow(model, config, logger)
        elif config["lib"] == "pytorch":
            return Pytorch(model, config, logger)
        else:
            raise Exception("Invalid deep learning interface type")