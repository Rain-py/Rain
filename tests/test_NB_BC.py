# the inclusion of the tests module is not meant to offer best practices for
# testing in general, but rather to support the `find_packages` example in
# setup.py that excludes installing the "tests" package

import unittest
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from Rain.Rain import Rain

def getData():
    X, y = load_breast_cancer(return_X_y=True)
    print(f"Breast cancer dataset shape: {X.shape}")

    for label in np.unique(y):
        print(f"Percentage of label ({label}) in the dataset is: {(np.sum(y == label) / len(y)).round(2)}")

    # split dataset into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y)
    return X_train, y_train, X_test, y_test

config = {
  "mode": {
      "type": "local",
      "params": {
        "num_of_workers": 2,
      }
    },
  "temp_data_path": "./",
  "partitions": 2,
  "iterations": 3,
  "chunk_size": 1024*1024,
  "learning_type": "ML",
  "ML": {
      "algorithm": {
      "type": "GaussianNaiveBayes",
    }  
  }
}
ACCURACY_THRESHOLD = 85
class TestRain(unittest.TestCase):

    def test_sync(self):
        # Prepare data
        X_train, y_train, X_test, y_test = getData()
        standard_scaler = StandardScaler()
        X_train = standard_scaler.fit_transform(X_train)
        X_test = standard_scaler.transform(X_test)

        # Train model
        rain = Rain(config)
        model = rain.train(X_train, y_train)

        # Evaluate the model
        y_pred = model.predict(X_test)
        accuracy = np.sum(y_pred == y_test) / len(y_test) * 100
        print(f"Accuracy of naive bayes classifier is: {accuracy.round(2)}%")

        self.assertGreater(accuracy, ACCURACY_THRESHOLD)



if __name__ == '__main__':
    unittest.main()

