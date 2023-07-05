import numpy
from typing import Tuple, List

from Rain.Divider.DividerAmbassador import DividerAmbassador
from Rain.Divider.DeepLearning.DeepLearningFactory import DeepLearningFactory
from Rain.Divider.MachineLearning.MachineLearningFactory import MachineLearningFactory
from Rain.TemporaryFilesManager.TemporaryFilesManager import TemporaryFilesManager
from Rain.LogService.LogService import LogService


class Divider:
    def __init__(self, config : dict, model : any) -> None:
        """
        Function to initialize the divider.
        Args:
            config (dict): configuration settings.
            model (any): the model to be trained.

        Raises:
            Exception: if the learning type is not supported.
        """
        self.num_of_workers = config["mode"]["params"]["num_of_workers"]
        self.partitions = config["partitions"]

        # create a logger for the divider.
        self.logger = LogService("Divider")

        # create a divider ambassador to serve the divider with other services.
        self.divider_ambassador = DividerAmbassador(chunk_size = config["chunk_size"])  

        # create a temporary directory for the divider to store its data.      
        self.model_base_path = TemporaryFilesManager.get_instance().create_temp_dir('divider/')

        # define the interface.
        if config["learning_type"] == "DL":
            self.algorithm = DeepLearningFactory.create_DL_interface(model, config, self.divider_ambassador)
        elif config["learning_type"] == "ML":
            self.algorithm = MachineLearningFactory.create_ML_interface(config, self.divider_ambassador)
        else: 
            raise Exception("Unknown learning type")

    def __del__(self) -> None:
        """
        Function to delete the divider all instance that are used.
        """
        try:
            del self.algorithm
            del self.divider_ambassador
            del self.logger
        except Exception as e:
            self.logger.log('error', f"Error deleting: {e}")

    def serve(self) -> None:
        """
        Function to start serving the divider.
        """
        self.divider_ambassador.serve()

    def stop_serving(self) -> None:
        """
        Function to stop serving the divider.
        """
        try:
            self.divider_ambassador.stop_serving()
            self.logger.log('debug', f"Divider stopped serving")
        except Exception as e:
            self.logger.log('error', "Error stopping serving: " + str(e))
            return


    def __partition_data(self, X : numpy.ndarray, y : numpy.ndarray) -> Tuple[List[numpy.ndarray], List[numpy.ndarray]]:
        """
        Private function to partition the data into subsets equal to the number of partitions passed.

        Args:
            X (numpy.ndarray): X data
            y (numpy.ndarray): y data

        Returns:
            tuple(list, list): X and y partitions
        """
        num_samples = X.shape[0]

        # to make the data independent and identically distributed (i.i.d.) subsets
        indices = numpy.random.permutation(num_samples) 

        # Use the shuffled indices to shuffle the datasets
        X = X[indices]
        y = y[indices]

        X_train_partitions = []
        y_train_partitions = []

        partition_size = int(len(X) / self.partitions)

        for i in range(self.partitions):
            if i == self.partitions - 1:
                X_train_partitions.append(X[i * partition_size :])
                y_train_partitions.append(y[i * partition_size :])
            else:
                X_train_partitions.append(X[i * partition_size : (i + 1) * partition_size])
                y_train_partitions.append(y[i * partition_size : (i + 1) * partition_size])

        return X_train_partitions, y_train_partitions

    def send_info_to_workers(self, iteration_num : int) -> None:
        """
        Function to send the model info to the workers.

        Args:
            iteration_num (int): the iteration number of the training.
        """
        self.algorithm.send_info_to_workers(iteration_num)

    def train(self, strategy : str, X : numpy.ndarray, y : numpy.ndarray) -> any:
        """
        Function to train the model.

        Args:
            strategy (str): strategy to update the model gradients.
            X (numpy.ndarray): X train data
            y (numpy.ndarray, optional): y train data. (if unsupervised, pass None)

        Raises:
            Exception: if the strategy is not valid. 

        Returns:
            any: the trained model.
        """
        if y is None:
            y = numpy.zeros(X.shape[0])
        
        # partition the data
        X_train_partitions, y_train_partitions = self.__partition_data(X, y)
        
        if strategy == 'sync':
            model = self.algorithm.train_centralized_sync(X_train_partitions, y_train_partitions)
        elif strategy == 'async':
            model = self.algorithm.train_centralized_async(X_train_partitions, y_train_partitions) 
        else:
            raise Exception("Invalid strategy")
        return model 


