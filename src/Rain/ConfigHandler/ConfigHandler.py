import os
import tensorflow as tf
import torch

class ConfigHandler:
    def __init__(self) -> None:
        self.config = None
    def validate_config(self, config):
        self.config = config
        self.check_temp_data_path()
        self.check_partitions()
        self.check_iterations()
        self.check_learning_type()
        self.check_mode()
    #________temp_data_path________
    def check_temp_data_path(self):
        try:
            if "temp_data_path" not in self.config:
                self.config["temp_data_path"] = None
                return
            if not os.path.exists(self.config["temp_data_path"]):
                raise Exception("temp_data_path does not exist")
        except Exception as e:
            raise Exception(f"Error in temp_data_path: {e}")
    #________partitions__________
    def check_partitions(self):
        # check that config["partitions"] is a valid integer
        try:
            if "partitions" not in self.config["partitions"]:
                self.config["partitions"] = 1
                return
            self.config["partitions"] = int(self.config["partitions"])
        except Exception as e:
            raise Exception(f"Error in partitions: {e}")
    #________iterations__________
    def check_iterations(self):
        # check that config["iterations"] is a valid integer
        try:
            if "iterations" not in self.config:
                self.config["iterations"] = 1
                return
            self.config["iterations"] = int(self.config["iterations"])
        except Exception as e:
            raise Exception(f"Error in iterations: {e}")
    #________learning_type________
    def check_learning_type(self):
        # check that config["learning_type"] is a valid string
        try:
            if "learning_type" not in self.config:
                raise Exception(f"Error in learning_type: Not specified")
            if self.config["learning_type"] not in ["DL", "ML"]:
                raise Exception(f"Error in learning_type: Not a valid learning type")
            if self.config["learning_type"] == "DL":
                self.check_DL()
            elif self.config["learning_type"] == "ML":
                self.check_ML()
        except Exception as e:
            raise Exception(f"Error in learning_type: {e}")
    def check_ML(self):
        try:
            if "ML" not in self.config:
                raise Exception(f"Error in ML: Not specified")
            if type(self.config["ML"]) != dict:
                raise Exception(f"Error in ML: Not a valid dictionary")
            if "algorithm" not in self.config["ML"]:
                raise Exception(f"Error in ML: algorithm is not specified")
            if type(self.config["ML"]["algorithm"]) != dict:
                raise Exception(f"Error in ML: algorithm is not a valid dictionary")
            if "type" not in self.config["ML"]["algorithm"]:
                raise Exception(f"Error in ML: algorithm type is not specified")
            if self.config["ML"]["algorithm"]["type"] not in ["KMeans", "SVM"]:
                raise Exception(f"Error in ML: Not a valid ML algorithm")
            if "params" not in self.config["ML"]["algorithm"]:
                raise Exception(f"Error in ML: algorithm params is not specified")
            if type(self.config["ML"]["algorithm"]["params"]) != dict:
                raise Exception(f"Error in ML: algorithm params is not a valid dictionary")
            if self.config["ML"]["algorithm"]["type"] == "KMeans":
                self.check_ML_algorithm_KMeans()
            elif self.config["ML"]["algorithm"]["type"] == "GaussianNaiveBayes":
                self.check_ML_algorithm_GaussianNaiveBayes()
        except Exception as e:
            raise Exception(f"Error in ML: {e}")
    def check_ML_algorithm_KMeans(self):
        try:
            if "K" not in self.config["ML"]["algorithm"]["params"]:
                raise Exception(f"Error in ML: K is not specified")
            self.config["ML"]["algorithm"]["params"]["K"] = int(self.config["ML"]["algorithm"]["params"]["K"])
        except Exception as e:
            raise Exception(f"Error in ML: {e}")
    def check_ML_algorithm_GaussianNaiveBayes(self):
        pass
    def check_DL(self):
        try:
            if "DL" not in self.config:
                raise Exception(f"Error in DL: Not specified")
            if type(self.config["DL"]) != dict:
                raise Exception(f"Error in DL: Not a valid dictionary")
            
            if "lr" not in self.config["DL"]:
                raise Exception(f"Error in DL: lr is not specified")
            self.config["DL"]["lr"] = float(self.config["DL"]["lr"])
            if "epochs" not in self.config["DL"]:
                raise Exception(f"Error in DL: epochs is not specified")
            self.config["DL"]["epochs"] = int(self.config["DL"]["epochs"])
            if "batch_size" not in self.config["DL"]:
                raise Exception(f"Error in DL: batch_size is not specified")
            self.config["DL"]["batch_size"] = int(self.config["DL"]["batch_size"])
            
            if "lib" not in self.config["DL"]:
                raise Exception(f"Error in DL: lib is not specified")
            if type(self.config["DL"]["lib"]) != dict:
                raise Exception(f"Error in DL: lib is not a valid dictionary")
            if "type" not in self.config["DL"]["lib"]:
                raise Exception(f"Error in DL: lib type is not specified")
            
            if self.config["DL"]["lib"]["type"] not in ["tensorflow", "pytorch"]:
                raise Exception(f"Error in DL: Not a valid DL library")
            if "params" not in self.config["DL"]["lib"]:
                raise Exception(f"Error in DL: lib params is not specified")
            if type(self.config["DL"]["lib"]["params"]) != dict:
                raise Exception(f"Error in DL: lib params is not a valid dictionary")
            if self.config["DL"]["lib"]["type"] == "tensorflow":
                self.check_DL_lib_tensorflow()
            elif self.config["DL"]["lib"]["type"] == "pytorch":
                self.check_DL_lib_pytorch()
        except Exception as e:
            raise Exception(f"Error in DL: {e}")
    def check_DL_lib_tensorflow(self):
        try:
            if "loss" not in self.config["DL"]["lib"]["params"]:
                raise Exception(f"Error in DL: loss is not specified")
            # check that loss is from the class tf.keras.losses
            if not isinstance(self.config["DL"]["lib"]["params"]["loss"], tf.keras.losses.Loss):
                raise Exception(f"Error in DL: loss is not a valid loss function")
            if "optimizer" not in self.config["DL"]["lib"]["params"]:
                raise Exception(f"Error in DL: optimizer is not specified")
            # check that optimizer is from the class tf.keras.optimizers
            if not isinstance(self.config["DL"]["lib"]["params"]["optimizer"], tf.keras.optimizers.Optimizer):
                raise Exception(f"Error in DL: optimizer is not a valid optimizer")
        except Exception as e:
            raise Exception(f"Error in DL: {e}")
    def check_DL_lib_pytorch(self):
        try:
            if "loss" not in self.config["DL"]["lib"]["params"]:
                raise Exception(f"Error in DL: loss is not specified")
            # check that loss is from the class torch.nn.modules.loss
            if not isinstance(self.config["DL"]["lib"]["params"]["loss"], torch.nn.modules.loss._Loss):
                raise Exception(f"Error in DL: loss is not a valid loss function")
            if "optimizer" not in self.config["DL"]["lib"]["params"]:
                raise Exception(f"Error in DL: optimizer is not specified")
            # check that optimizer is from the class torch.optim
            if not isinstance(self.config["DL"]["lib"]["params"]["optimizer"], torch.optim.Optimizer):
                raise Exception(f"Error in DL: optimizer is not a valid optimizer")
        except Exception as e:
            raise Exception(f"Error in DL: {e}")
    #_________mode________________
    def check_mode(self):
        # check that config["mode"] is a valid dictionary
        try:
            if "mode" not in self.config:
                self.config["mode"] = {
                    "type": "local",
                    "params": {
                        "num_of_workers": 1
                    }
                }
            if type(self.config["mode"]) != dict:
                raise Exception(f"Error in mode: {e}")
            # check that mode is belong to: (local, cloud, lazy)
            if self.config["mode"]["type"] not in ["local",  "lazy", "cloud"]:
                raise Exception(f"Error in mode: Not a valid mode")
            if "params" not in self.config["mode"]:
                raise Exception(f"Error in mode: No params specified")
            if type(self.config["mode"]["params"]) != dict:
                raise Exception(f"Error in mode: params is not a valid dict")
            if self.config["mode"]["type"] == "local":
                self.check_mode_local()
            elif self.config["mode"]["type"] == "lazy":
                self.check_mode_lazy()
            elif self.config["mode"]["type"] == "cloud":
                self.check_mode_cloud()
        except Exception as e:
            raise Exception(f"Error in mode: {e}")
    def check_mode_local(self):
        try:
            if "num_of_workers" not in self.config["mode"]["params"]:
                raise Exception(f"Error in params: num_of_workers is not specified")
            # check that config["mode"]["params"]["num_of_workers"] is a valid integer
            self.config["mode"]["params"]["num_of_workers"] = int(self.config["mode"]["params"]["num_of_workers"])
        except Exception as e:
            raise Exception(f"Error in mode: {e}")
    def check_mode_lazy(self):
        try:
            if "num_of_workers" not in self.config["mode"]["params"]:
                raise Exception(f"Error in params: num_of_workers is not specified")
            # check that config["mode"]["params"]["num_of_workers"] is a valid integer
            self.config["mode"]["params"]["num_of_workers"] = int(self.config["mode"]["params"]["num_of_workers"])
            if "ips" not in self.config["mode"]["params"]:
                raise Exception(f"Error in params: ips is not specified")
            # check that config["mode"]["params"]["ips"] is a valid list
            if type(self.config["mode"]["params"]["ips"]) != list:
                raise Exception(f"Error in params: ips is not a valid list")
            if "ports" not in self.config["mode"]["params"]:
                raise Exception(f"Error in params: ports is not specified")
            # check that config["mode"]["params"]["ports"] is a valid list
            if type(self.config["mode"]["params"]["ports"]) != list:
                raise Exception(f"Error in params: ports is not a valid list")
            # check that they are consistent in size
            if len(self.config["mode"]["params"]["ips"]) != len(self.config["mode"]["params"]["ports"]) \
            or len(self.config["mode"]["params"]["ips"]) != self.config["mode"]["params"]["num_of_workers"]\
            or len(self.config["mode"]["params"]["ports"]) != self.config["mode"]["params"]["num_of_workers"]:
                raise Exception(f"Error in params: ips and ports are not consistent in size with the number of workers")
        except Exception as e:
            raise Exception(f"Error in mode: {e}")
    def check_mode_cloud(self):
        try:
            if "num_of_workers" not in self.config["mode"]["params"]:
                raise Exception(f"Error in params: num_of_workers is not specified")
            # check that config["mode"]["params"]["num_of_workers"] is a valid integer
            self.config["mode"]["params"]["num_of_workers"] = int(self.config["mode"]["params"]["num_of_workers"])
            if "subscription_id" not in self.config["mode"]["params"]:
                raise Exception(f"Error in params: subscription_id is not specified")
            if "location" not in self.config["mode"]["params"]:
                raise Exception(f"Error in params: location is not specified")
        except Exception as e:
            raise Exception(f"Error in mode: {e}")

# Config example:
'''
config = {
    "mode": {
      "type": "lazy",
      "params": {
        "num_of_workers": 1,
        "ips": ['127.0.0.1'],
        "ports": [50151]
      }
    },
    "temp_data_path": "../../../",
    "partitions": 1,
    "iterations": 1,
    "learning_type": "DL",
    "DL": {
    "lib": {
      "type": "tensorflow",
      "params": {
        "loss": tf.keras.losses.CategoricalCrossentropy(),
        "optimizer": tf.keras.optimizers.Adam(learning_rate=0.001),

                }
            },
    "ML":   {
      "algorithm": {
      "type": "KMeans",
      "params": {
        "K": 2,
                }
                    }    
            }
    "lr": 0.001,
    "epochs": 1,
    "batch_size": 128,
  }
}
'''