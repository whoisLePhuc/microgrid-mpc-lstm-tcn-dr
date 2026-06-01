import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

class TCNBlock(layers.Layer):
    def __init__(self, filters, dilation_rate, kernel_size=3, dropout=0.2, **kwargs):
        super().__init__(**kwargs)
        self.filters = filters
        self.dilation_rate = dilation_rate
        self.kernel_size = kernel_size
        self.dropout_rate = dropout
        self.conv1 = layers.Conv1D(filters, kernel_size,
                                   dilation_rate=dilation_rate, padding='same')
        self.conv2 = layers.Conv1D(filters, kernel_size,
                                   dilation_rate=dilation_rate*2, padding='same')
        self.relu = layers.ReLU()
        self.dropout = layers.Dropout(dropout)
        self.norm = layers.LayerNormalization()
        self.skip = layers.Conv1D(filters, 1)

    def call(self, x, training=False):
        r = self.skip(x)
        x = self.relu(self.norm(self.conv1(x)))
        x = self.dropout(x, training=training)
        x = self.relu(self.norm(self.conv2(x)))
        x = self.dropout(x, training=training)
        return self.relu(x + r)

    def get_config(self):
        config = super().get_config()
        config.update({
            'filters': self.filters,
            'dilation_rate': self.dilation_rate,
            'kernel_size': self.kernel_size,
            'dropout': self.dropout_rate,
        })
        return config

class TCNStack(layers.Layer):
    def __init__(self, filters=128, blocks=3, kernel_size=3, dropout=0.2, **kwargs):
        super().__init__(**kwargs)
        self.filters = filters
        self.blocks_count = blocks
        self.kernel_size = kernel_size
        self.dropout_rate = dropout
        self.blocks = [TCNBlock(filters, 2**i, kernel_size, dropout)
                       for i in range(blocks)]

    def call(self, x, training=False):
        for b in self.blocks:
            x = b(x, training=training)
        return x

    def get_config(self):
        config = super().get_config()
        config.update({
            'filters': self.filters,
            'blocks': self.blocks_count,
            'kernel_size': self.kernel_size,
            'dropout': self.dropout_rate,
        })
        return config

class LSTMTCN:
    def __init__(self, input_steps=12, n_features=6, n_targets=5, horizon=4):
        self.input_steps = input_steps
        self.n_features = n_features
        self.n_targets = n_targets
        self.horizon = horizon
        self.model = None

    def build(self):
        inputs = keras.Input(shape=(self.input_steps, self.n_features))
        x = layers.LSTM(256, return_sequences=True)(inputs)
        x = layers.Dropout(0.2)(x)
        x = layers.LSTM(64, return_sequences=True)(x)
        x = layers.Dropout(0.2)(x)
        x = TCNStack(128, 3, 3, 0.2)(x)
        x = layers.Flatten()(x)
        x = layers.Dense(self.horizon * self.n_targets)(x)
        x = layers.Reshape((self.horizon, self.n_targets))(x)
        self.model = keras.Model(inputs, x)
        self.model.compile(optimizer=keras.optimizers.Adam(0.001), loss='mse')
        return self.model

    def train(self, X_train, y_train, X_val, y_val,
              epochs=100, batch_size=100):
        if self.model is None:
            self.build()
        cb = [keras.callbacks.EarlyStopping(
            patience=10, restore_best_weights=True)]
        return self.model.fit(X_train, y_train, validation_data=(X_val, y_val),
                            epochs=epochs, batch_size=batch_size,
                            callbacks=cb, verbose=1)

    def predict(self, X):
        if self.model is None:
            raise ValueError('Model not built/trained')
        return self.model.predict(X, verbose=0)

    def forecast_step(self, history):
        X = history[-self.input_steps:].reshape(
            1, self.input_steps, self.n_features)
        pred = self.predict(X)
        return {
            'p_pv': pred[0, :, 0], 'p_wind': pred[0, :, 1],
            'temp': pred[0, :, 2], 'load': pred[0, :, 3],
            'price': pred[0, :, 4],
        }

    def save(self, path):
        self.model.save(path)

    def load(self, path):
        self.model = keras.models.load_model(
            path, custom_objects={'TCNBlock': TCNBlock, 'TCNStack': TCNStack})
