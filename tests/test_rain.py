# the inclusion of the tests module is not meant to offer best practices for
# testing in general, but rather to support the `find_packages` example in
# setup.py that excludes installing the "tests" package

import unittest
import numpy as np
import sys
sys.path.append("../src/")
from Rain.Rain import Rain
sys.path.pop()

from keras.models import Sequential
from keras.layers import Dense, Activation, Dropout
import tensorflow as tf

import os
from keras.datasets import mnist
from keras.utils import to_categorical
import numpy as np

def getData():
    (X_train, y_train),(X_test, y_test) = mnist.load_data()
    y_train = to_categorical(y_train)
    y_test = to_categorical(y_test)

    image_size = X_train.shape[1]
    input_size = image_size * image_size

    X_train = np.reshape(X_train, [-1, input_size])
    X_train = X_train.astype('float32') / 255
    X_test = np.reshape(X_test, [-1, input_size])
    X_test = X_test.astype('float32') / 255

    # create a dir called data if it does not exist
    if not os.path.exists('./data'):
        os.makedirs('./data')
    return X_train, y_train, X_test, y_test
def create_model():
    # network parameters
    hidden_units = 256
    dropout = 0.45
    input_size = 784
    num_labels = 10
    # model is a 3-layer MLP with ReLU and dropout after each layer
    model = Sequential()
    model.add(Dense(hidden_units, input_dim=input_size))
    model.add(Activation("relu"))
    model.add(Dropout(dropout))
    model.add(Dense(hidden_units))
    model.add(Activation("relu"))
    model.add(Dropout(dropout))
    model.add(Dense(num_labels))
    model.add(Activation("softmax"))
    return model

config = {
  "mode": {
      "type": "local",
      "params": {}

    },
  "partitions": 3,
  "num_of_workers": 3,
  "iterations": 3,
  "learning_type": "DL",
  "DL": {
    "lib": {
      "type": "tensorflow",
      "params": {
        "loss": tf.keras.losses.CategoricalCrossentropy(),
        "optimizer": tf.keras.optimizers.Adam(learning_rate=0.001),

      }
    },
    "lr": 0.001,
    "epochs": 10,
    "batch_size": 128,
  }
}
class TestRain(unittest.TestCase):

    def test_sync(self):
        model = create_model()
        rain = Rain(config, model)
        X_train, y_train, X_test, y_test = getData()
        model = rain.train(X_train, y_train, strategy='sync')
        loss, acc = model.evaluate(X_test, y_test, batch_size=config["DL"]["batch_size"])
        print("\nTest accuracy: %.1f%%" % (100.0 * acc))
        self.assertEqual(1557, 1557)



if __name__ == '__main__':
    unittest.main()

