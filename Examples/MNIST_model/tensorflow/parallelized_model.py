# -*- coding: utf-8 -*-

import sys
import numpy as np

# sys.path.append("../../../src/")
from Rain.Rain import Rain
# sys.path.pop()

from keras.models import Sequential
from keras.layers import Dense, Activation, Dropout
import tensorflow as tf

import os
from keras.datasets import mnist
from keras.utils import to_categorical
import numpy as np
import os

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


np.save('./data/train_data.npy', X_train)
np.save('./data/train_labels.npy', y_train)
np.save('./data/test_data.npy', X_test)
np.save('./data/test_labels.npy', y_test)


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
    "epochs": 1,
    "batch_size": 128,
  }
}

def get_train_data():
    return np.load("./data/train_data.npy"), np.load(
        "./data/train_labels.npy"
    )
def get_test_data():
    return np.load("./data/test_data.npy"), np.load(
        "./data/test_labels.npy"
    )
X_train, y_train = get_train_data()

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


model = create_model()
rain = Rain(config, model)

model = rain.train(X_train, y_train, strategy='async')

X_test, y_test = get_test_data()
loss, acc = model.evaluate(X_test, y_test, batch_size=config["DL"]["batch_size"])
print("\nTest accuracy: %.1f%%" % (100.0 * acc))



# model = rain.train(X_train, y_train, strategy='sync')

# X_test, y_test = get_test_data()
# loss, acc = model.evaluate(X_test, y_test, batch_size=config["DL"]["batch_size"])
# print("\nTest accuracy: %.1f%%" % (100.0 * acc))
