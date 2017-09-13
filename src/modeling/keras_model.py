from __future__ import division, print_function

from utility.s3_mongo_inter import S3MongoInterface
from parsing.output_translation import OutputLayerExtractor as OLE

from keras import optimizers
from keras.models import Sequential, load_model
from keras.layers import Dense, Dropout, Activation, LSTM
from keras.layers.wrappers import TimeDistributed
from keras.layers.embeddings import Embedding
from keras.layers.noise import GaussianNoise
from keras.preprocessing import sequence

import numpy as np
import os


# REVIEW: Peephole?: https://github.com/fchollet/keras/issues/1717

class Model(object):

    note_count_len = 10

    truncated_backprop_length = 128
    batch_size = 50

    # LSTM cell
    state_size = 10
    num_add_layers = 3  # Don't think more layers are necessary

    input_size = 138
    hidden_dimension = 400
    output_size = 138

    stateful = False

    def __init__(
        self, attempt_reload=False, save_name='tmp/keras_model',
        num_epochs=50, learning_rate=0.01, additional_filter_song={}
    ):
        self.song_filter_query = additional_filter_song

        self.num_epochs = num_epochs
        self.learning_rate = learning_rate

        # data source interface
        self.interface = S3MongoInterface()

        # Save location
        modeling_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_path = os.path.join(modeling_dir, save_name)

        if attempt_reload:
            print("loading model")
            self.model = load_model(self.model_path + '.h5')

    def _generate_data(self):
        depth = int(self.truncated_backprop_length)
        current_song = self.interface.get_input_arrays(self.song_filter_query)
        while True:
            cur_data = current_song.next()
            for i in xrange(0, len(cur_data) - depth - 1, 1):
                # print(i)
                X = cur_data[i:i+depth]
                y = cur_data[i+1+depth]
                yield X, y

    def _data_batch(self):
        data_generator = self._generate_data()
        while True:
            X, y = data_generator.next()
            xs = [X]
            ys = [y]
            for i in range(self.batch_size - 1):
                X_new, y_new = data_generator.next()
                xs.append(X_new)
                ys.append(y_new)
            X = np.stack(xs, axis=0)
            y = np.stack(ys, axis=0)
            yield X, y

    def _protected_data_batch(self):
        """Generator that will yield data forever"""
        try:
            yield self._data_batch().next()
        except StopIteration:
            yield self._data_batch().next()

    def build_model(self):
        """
        Excellent Keras model guide:
        https://keras.io/getting-started/sequential-model-guide/
        """
        model = Sequential()
        model.add(GaussianNoise(0.2, input_shape=(self.truncated_backprop_length, self.input_size)))  # Does noise help prevent song overfitting?
        model.add(
            LSTM(
                self.batch_size,
                return_sequences=True,
                input_shape=(self.truncated_backprop_length, self.input_size),
                unit_forget_bias=True
                # batch_size=self.batch_size, stateful=True
            )
        )
        model.add(Dropout(0.1))
        model.add(TimeDistributed(Dense(
            input_dim=self.input_size,
            units=self.hidden_dimension
        )))
        # for _ in range(self.num_add_layers):
        #     model.add(Dropout(0.01))
        #     model.add(LSTM(
        #         input_shape=(self.hidden_dimension,), units=self.hidden_dimension,
        #         return_sequences=True
        #     ))
        #     model.add(Dense(
        #         input_dim=self.input_size,
        #         units=self.hidden_dimension
        #     ))
        model.add(LSTM(
            self.hidden_dimension, return_sequences=False,
            unit_forget_bias=True
            # batch_size=self.batch_size, stateful=True
        ))
        model.add(Dropout(0.1))
        model.add(Dense(self.output_size))
        model.add(Activation('sigmoid'))

        # opt = optimizers.Adagrad(lr=self.learning_rate)  # NOTE: This overfits songs!
        # optsgd = optimizers.SGD(lr=self.learning_rate, momentum=1e-5)
        optrms = optimizers.RMSprop(lr=self.learning_rate)
        model.compile(
            loss='categorical_crossentropy', optimizer=optrms,  # binary vs. categorical?
            metrics=['accuracy']
        )
        self.model = model

    def fit_model(
        self, save=False, num_epochs_per_iter=100, save_model_hist=False,
        save_every=500
    ):
        self.build_model()
        iteration = 0
        data_batch_gen = self._data_batch()
        while iteration < self.num_epochs:
            X, y = data_batch_gen.next()
            history = self.model.fit(X, y, batch_size=self.batch_size, epochs=num_epochs_per_iter)
            iteration += num_epochs_per_iter
            if save_model_hist and iteration % save_every == 0:
                self.model.save(self.model_path + '_' + str(iteration) + '.h5')
        if save:
            print("Saving")
            self.model.save(self.model_path + '.h5')

    def _note_count_index(self, note_count):
        if note_count >= 9:
            return 9
        elif note_count <= 0:
            return 0
        else:
            return note_count

    def _get_note_count_hot(self, note_count):
        """
        Given a note_count int returns an array of len 10 to append to the end
        of the input layer so the number of notes to select can be determined during playback
        """
        result = np.zeros(10)
        result[self._note_count_index(note_count)] = 1
        return result

    def _convert_to_input_layer(self, input_size, pred_out_layer):
        result = np.zeros(128)
        note_count = pred_out_layer[:,-self.note_count_len:].argmax()
        notes = pred_out_layer[:,:-self.note_count_len].argsort(axis=1)[:,-note_count:][::-1]
        result[notes] = 1
        num_result = self._get_note_count_hot(note_count)
        result = np.hstack([result, num_result])
        return result

    def predict_output(self, seed, beat_length):
        # if not self.stateful:
        logits_list = list()
        for i in range(beat_length):
            X = seed[-self.truncated_backprop_length:,:]
            # import pdb; pdb.set_trace()
            new_logit = self.model.predict(X.reshape((1, self.truncated_backprop_length, self.input_size)))
            logits_list.append(new_logit)
            seed = np.vstack([seed, self._convert_to_input_layer(self.input_size, new_logit)])
            # import pdb; pdb.set_trace()
        return seed, logits_list
        # else:
        #     logits_list = list()
        #     for i in range(beat_length):
        #         # Duplicate seed to be the same for all batches
        #         Xs = [seed[-self.truncated_backprop_length:,:]] * self.batch_size
        #         X = np.stack(Xs, axis=0)
        #         new_logit = self.model.predict(X.reshape((self.batch_size, self.truncated_backprop_length, self.input_size)))
        #         logits_list.append(new_logit)
        #         seed = np.vstack([seed, self._convert_to_input_layer(self.input_size, new_logit)])
        #         # import pdb; pdb.set_trace()
        #     return seed, logits_list
