# the inclusion of the tests module is not meant to offer best practices for
# testing in general, but rather to support the `find_packages` example in
# setup.py that excludes installing the "tests" package

import unittest
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier as KNN_classifier_sklearn
from Rain.Divider.MachineLearning.KNN import KNN as KNN_classifier_rain


def getData():
    X, y = load_breast_cancer(return_X_y=True)
    print(f"Breast cancer dataset shape: {X.shape}")

    for label in np.unique(y):
        print(f"Percentage of label ({label}) in the dataset is: {(np.sum(y == label) / len(y)).round(2)}")

    # split dataset into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y)
    return X_train, y_train, X_test, y_test

class TestML(unittest.TestCase):

    def test_NB(self):
        # Prepare data
        X_train, y_train, X_test, y_test = getData()
        standard_scaler = StandardScaler()
        X_train = standard_scaler.fit_transform(X_train)
        X_test = standard_scaler.transform(X_test)

        # Train the Sklearn model
        knn_classifier = KNN_classifier_sklearn(n_neighbors=5, metric= "euclidean")
        knn_classifier.fit(X_train, y_train)
        # Evaluate the Sklearn model
        y_pred_sklearn = knn_classifier.predict(X_test)
        accuracy_sklearn = (np.sum(y_pred_sklearn == y_test) / len(y_test) * 100).round(2)
        print(f"Accuracy of Sklearn kNN classifier is: {accuracy_sklearn}%")
        
        # Train the Rain model
        knn_classifier = KNN_classifier_rain(n_neighbors=5, metric= "euclidean")
        knn_classifier.fit(X_train, y_train)
        # Evaluate the Rain model
        y_pred_rain = knn_classifier.predict(X_test)
        accuracy_rain = (np.sum(y_pred_rain == y_test) / len(y_test) * 100).round(2)
        print(f"Accuracy of Rain kNN classifier is: {accuracy_rain}%")

        # Assert that the ratio between them is more than 0.95
        self.assertTrue(accuracy_rain / accuracy_sklearn > 0.95)

        




if __name__ == '__main__':
    unittest.main()

