import numpy as np
from Rain.Rain import Rain
import sys

from keras.models import Sequential
from keras.layers import Dense, Activation, Dropout
import tensorflow as tf

from keras.layers import Conv2D
from keras.layers import MaxPooling2D
from keras.layers import Dense
from keras.layers import Flatten
from keras.layers import Dropout
from keras.optimizers import SGD
from keras.losses import CategoricalCrossentropy

import os
from keras.datasets import cifar10, mnist
from keras.utils import to_categorical
import numpy as np

def getData(dataset='mnist'):
    if dataset == 'mnist':
      (X_train, y_train),(X_test, y_test) = mnist.load_data()
    else:
      (X_train, y_train),(X_test, y_test) = cifar10.load_data()
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

def create_cifar():
    model = Sequential()
    model.add(Conv2D(32, (3, 3), activation='relu', kernel_initializer='he_uniform', padding='same', input_shape=(32, 32, 3)))
    model.add(Conv2D(32, (3, 3), activation='relu', kernel_initializer='he_uniform', padding='same'))
    model.add(MaxPooling2D((2, 2)))
    model.add(Dropout(0.2))
    model.add(Conv2D(64, (3, 3), activation='relu', kernel_initializer='he_uniform', padding='same'))
    model.add(Conv2D(64, (3, 3), activation='relu', kernel_initializer='he_uniform', padding='same'))
    model.add(MaxPooling2D((2, 2)))
    model.add(Dropout(0.2))
    model.add(Conv2D(128, (3, 3), activation='relu', kernel_initializer='he_uniform', padding='same'))
    model.add(Conv2D(128, (3, 3), activation='relu', kernel_initializer='he_uniform', padding='same'))
    model.add(MaxPooling2D((2, 2)))
    model.add(Dropout(0.2))
    model.add(Flatten())
    model.add(Dense(128, activation='relu', kernel_initializer='he_uniform'))
    model.add(Dropout(0.2))
    model.add(Dense(10, activation='softmax'))
    return model


def create_mnist():
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
      "type": "lazy",
      "params": {
        "num_of_workers": 3,
        "ips": ['172.190.116.144', '172.190.116.144', '172.190.116.144'], #[,'127.0.0.1', '127.0.0.1', '127.0.0.1'], 
        "ports": [50151, 50152, 50153]
        
      }
    },
  "temp_data_path": "./",
  "partitions": 3,
  "iterations": 3,
  "chunk_size": 1024*1024,
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
    "epochs": 5,
    "batch_size": 128,
  }
}
def main():
    if sys.argv[1] == 'cifar':
      model = create_cifar()
      X_train, y_train, X_test, y_test = getData('cifar')
    else:
      model = create_mnist()
      X_train, y_train, X_test, y_test = getData('mnist')
    rain = Rain(config, model)
    model = rain.train(X_train, y_train, strategy='sync')
    loss, acc = model.evaluate(X_test, y_test, batch_size=config["DL"]["batch_size"])
    print("\nTest accuracy: %.1f%%" % (100.0 * acc))

if __name__ == '__main__':
    main()
