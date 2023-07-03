import torch
import numpy as np
from Rain.Divider.DeepLearning.DeepLearningInterface import DeepLearningInterface

class Pytorch(DeepLearningInterface):
    def __init__(self, model, config, divider_ambassador):
        super().__init__(model, config, divider_ambassador)

    def reduce_gradients_sync(self, gradients):
        # find the old weights
        weights = [param.clone().detach().numpy() for param in self.model.parameters()]  
        try:
            # Average the gradients
            gradient_avg = []
            for gradient_list_tuple in zip(*gradients):
                gradient_avg.append(np.array([np.array(g).mean(axis=0) for g in zip(*gradient_list_tuple)]))
        
        except Exception as e:
            self.logger.log('debug', f"Error in reducing the gradients: {e}")
            return

        try:
            # weight(new) = weight(old) — LR * gradients_average
            weights = [weights[i] - self.lr * gradient_avg[i] for i in range(len(weights))]
            
            # set the new weights
            state_dict = self.model.state_dict()
            for key, value in zip(state_dict.keys(), weights):
                state_dict[key] = torch.from_numpy(value)

            self.model.load_state_dict(state_dict)
        
        except Exception as e:
            self.logger.log('debug', f"Error in calculating the new weights: {e}")
            return


    def reduce_gradients_async(self, gradient, worker_id):
        # find the old weights
        weights = [param.clone().detach().numpy() for param in self.model.parameters()]  

        try:
            # weight(new) = weight(old) — (LR / number_of_workers) * gradient
            weights = [weights[i] - (self.lr / self.num_of_workers) * gradient[i] for i in range(len(weights))]
            
            # set the new weights
            state_dict = self.model.state_dict()
            for key, value in zip(state_dict.keys(), weights):
                state_dict[key] = torch.from_numpy(value)

            self.model.load_state_dict(state_dict)
            self.logger.log('debug', f"Asynchronous update is done by worker {worker_id}")

        except Exception as e:
            self.logger.log('debug', f"Error in calculating the new weights: {e}")
            return