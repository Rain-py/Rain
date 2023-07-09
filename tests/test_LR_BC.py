# the inclusion of the tests module is not meant to offer best practices for
# testing in general, but rather to support the `find_packages` example in
# setup.py that excludes installing the "tests" package

import unittest
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from Rain.Divider.MachineLearning.LogisticRegression import LogisticRegression as logistic_regression_classifier_rain
from Rain.Rain import Rain

def getData():
    X, y = load_breast_cancer(return_X_y=True)
    print(f"Breast cancer dataset shape: {X.shape}")

    # for label in np.unique(y):
    #     print(f"Percentage of label ({label}) in the dataset is: {(np.sum(y == label) / len(y)).round(2)}")

    # split dataset into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y)
    return X_train, y_train, X_test, y_test

class TestML(unittest.TestCase):

    def test_LR(self):
        # Prepare data
        X_train, y_train, X_test, y_test = getData()
        standard_scaler = StandardScaler()
        X_train = standard_scaler.fit_transform(X_train)
        X_test = standard_scaler.transform(X_test)

        config = {
                "mode": {
                    "type": "local",
                    "params": {
                        "num_of_workers": 3,
                    }
                },
                "temp_data_path": "../",
                "partitions": 3,
                "iterations": 50,
                "chunk_size": 1024*1024,
                "learning_type": "ML",
                "ML": {
                    "algorithm": {
                    "type": "LogisticRegression",
                    "params": {
                        "lr": 0.01
                    }
                }    
            }
        }
        # Train the standard model
        logistic_regression_classifier = logistic_regression_classifier_rain(learning_rate=config["ML"]["algorithm"]["params"]["lr"], max_iters=config["iterations"])
        logistic_regression_classifier.fit(X_train, y_train)
        # Evaluate the standard model
        y_pred_standard = logistic_regression_classifier.predict(X_test)
        accuracy_standard = (np.sum(y_pred_standard == y_test) / len(y_test) * 100).round(2)
        print(f"Accuracy of standard logistic regression classifier is: {accuracy_standard}%")
        
        # Train the Rain model
        rain = Rain(config)
        rain_classifier = rain.train(X_train, y_train)
        # Evaluate the Rain model
        y_pred_rain = rain_classifier.predict(X_test)
        accuracy_rain = (np.sum(y_pred_rain == y_test) / len(y_test) * 100).round(2)
        print(f"Accuracy of Rain naive bayes classifier is: {accuracy_rain}%")

        # Assert that the two models produce the same results
        self.assertTrue((y_pred_rain == y_pred_standard).sum() == len(y_pred_standard))
        del rain

        




if __name__ == '__main__':
    unittest.main()

