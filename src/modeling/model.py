from __future__ import division, print_function

from utility.s3_mongo_inter import S3MongoInterface

import tensorflow as tf
import numpy as np
import os
import cPickle as pickle


class SimpleModel(object):

    def __init__(self, num_epochs=200):
        self.truncated_backprop_length = 25
        self.batch_size = 1
        self.num_epochs = num_epochs
        self.learning_rate = 0.3

        # LSTM cell
        self.state_size = 100
        self.num_layers = 3

        self.input_size = 138
        self.output_size = 138

        # data source interface
        self.interface = S3MongoInterface()

        # List to collect losses as they're calculated
        self.loss_list = []

        modeling_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_path = os.path.join(modeling_dir, 'tmp')

    def _generate_data(self):
        depth = int(self.truncated_backprop_length)
        cur_data = self.interface.get_input_arrays({}).next()
        for i in range(0, len(cur_data) - depth - 1, 1):
            X = cur_data[i:i+depth]
            y = cur_data[i+1+depth]
            yield X, y

    def _data_batch(self):
        X, y = self._generate_data().next()
        for i in range(self.batch_size - 1):
            X_new, y_new = self._generate_data().next()
            X = np.vstack([X, X_new])
            y = np.vstack([y, y_new])
        yield X.reshape((self.batch_size, -1)), y.reshape((self.batch_size, -1))

    def _protected_data_batch(self):
        """Generator that will yield data forever"""
        try:
            yield self._data_batch().next()
        except StopIteration:
            yield self._data_batch().next()


    def _build_graph(self):
        # Batch size?
        # Truncated backprop for vanishing gradient problem
        X = tf.placeholder(
            tf.float32,
            [self.batch_size, self.truncated_backprop_length * self.input_size],
            name='X'
        )  # trunc backrpop is the number of beats to look back for diminishing gradient problem
        # This is x rolled forward by 1
        y = tf.placeholder(
            tf.float32,
            [self.batch_size, self.input_size],
            name='y'
        )

        # 2 corresponds to visible and hidden
        init_state = tf.placeholder(
            tf.float32,
            [self.num_layers, 2, self.batch_size, self.state_size]
        )
        state_per_layer_list = tf.unstack(init_state, axis=0)
        rnn_tuple_state = tuple(
            [tf.nn.rnn_cell.LSTMStateTuple(state_per_layer_list[idx][0,:,:], state_per_layer_list[idx][1,:,:])
            for idx in range(self.num_layers)]
        )

        W2 = tf.Variable(
            np.random.rand(self.state_size, self.output_size),
            dtype=tf.float32, name="W2"
        )
        b2 = tf.Variable(
            np.zeros((1, self.output_size)),
            dtype=tf.float32, name="b2"
        )

        stacked_rnn = []
        for _ in range(self.num_layers):
            stacked_rnn.append(tf.nn.rnn_cell.LSTMCell(
                self.state_size, state_is_tuple=True, reuse=tf.get_variable_scope().reuse
            ))
        lstm_cells = tf.nn.rnn_cell.MultiRNNCell(
            stacked_rnn,
            state_is_tuple=True
        )

        states_series, current_state = tf.nn.dynamic_rnn(
            lstm_cells,
            tf.expand_dims(X, -1),
            initial_state=rnn_tuple_state
        )

        states_series = tf.reshape(states_series, [-1, self.state_size])

        logits = tf.matmul(states_series, W2) + b2

        logits = tf.reshape(
            logits,
            [self.batch_size, self.input_size * self.truncated_backprop_length, self.input_size],
        )
        labels = y

        logits_series = tf.unstack(logits, axis=1)
        predictions_series = [
            tf.nn.sigmoid(logits) for logits in logits_series
        ]

        losses = tf.nn.sigmoid_cross_entropy_with_logits(
            logits=logits, labels=labels
        )
        total_loss = tf.reduce_mean(losses)

        train_step = tf.train.AdagradOptimizer(self.learning_rate).minimize(total_loss)

        instance_vars = [total_loss, train_step, current_state, predictions_series, X, y, init_state]
        model_vars = [W2, b2]
        return instance_vars, model_vars

    def _save_model_params(self, sess, W2, b2, current_state):
        """Accepts pointers to model parameter tensors and other objects and saves to disk"""
        with open(os.path.join(self.model_path, 'W2.pkl'), 'wb') as f:
            pickle.dump(W2.eval(session=sess), f)
        with open(os.path.join(self.model_path, 'b2.pkl'), 'wb') as f:
            pickle.dump(b2.eval(session=sess), f)
        with open(os.path.join(self.model_path, 'current_state'), 'wb') as f:
            pickle.dump(current_state, f)
        # Current state consists of tensor arranged in num_layers x 2
        # for layer_idx, _ in enumerate(current_state):
        #     for hidden in range(2):
        #         with open(
        #             os.path.join(self.model_path, 'current_state_{}_{}.pkl'.format(layer_idx, hidden)),
        #             'wb'
        #         ) as f:
        #             pickle.dump(current_state[layer_idx][hidden].eval(session=sess), f)

    def _load_model_params(self):
        with open(os.path.join(self.model_path, 'W2.pkl'), 'rb') as f:
            W2 = pickle.load(f)
        with open(os.path.join(self.model_path, 'b2.pkl'), 'rb') as f:
            b2 = pickle.load(f)
        with open(os.path.join(self.model_path, 'current_state'), 'rb') as f:
            current_state = pickle.load(f)
        # current_state_lst = []
        # for layer_idx in range(self.num_layers):
        #     for hidden in range(2):
        #         with open(
        #             os.path.join(self.model_path, 'current_state_{}_{}.pkl'.format(layer_idx, hidden)),
        #             'rb'
        #         ) as f:
        #             current_state_lst.append(pickle.load(f))
        # current_state = tuple([
        #     tuple(
        #         current_state_lst[i], current_state_lst[i+1]
        #     )
        #     for i in range(0, len(current_state_lst), 2)
        # ])
        return W2, b2, current_state

    def train(self, save=True):
        instance_vars, model_vars = self._build_graph()

        total_loss, train_step, current_state, predictions_series, X, y, init_state = instance_vars
        W2, b2 = model_vars
        print("Starting training")
        with tf.Session() as sess:

            init = tf.global_variables_initializer()
            sess.run(init)

            saved_state = tf.get_variable('saved_state', shape=[self.num_layers, 2, self.batch_size, self.state_size])

            saver = tf.train.Saver(max_to_keep=1)

            # Does it make sense to reset the state here like this? stateless/stateful or no difference?
            _current_state = np.zeros((self.num_layers, 2, self.batch_size, self.state_size))

            for epoch in range(self.num_epochs):
                # Initialize inputs
                X_, y_ = self._protected_data_batch().next()

                # One step
                _total_loss, _train_step, _current_state, _predictions_series = sess.run(
                    [total_loss, train_step, current_state, predictions_series],
                    feed_dict={
                        X: X_,
                        y: y_,
                        init_state: _current_state
                    })
                self.loss_list.append(_total_loss)

                if epoch % 10 == 0:
                    print("Epoch", epoch, "loss:", _total_loss)
            if save:
                print("saving")
                # import pdb; pdb.set_trace()
                # _current_state is tuple of len num_layers, consisting of tuples of len 2, consisting of arrays of len state_size
                final_state = np.array([[t for t in st] for st in _current_state])

                assign_op = tf.assign(saved_state, final_state)
                sess.run(assign_op)
                saver.save(sess, self.model_path + '/model.ckpt')

                self._save_model_params(sess, W2, b2, _current_state)

        print("Done")

    def truncate_music_seed(self, X_seed):
        assert X_seed.shape[1] == self.input_size, "Invalid seed shape {}".format(X_seed.shape)
        length_difference = self.truncated_backprop_length - X_seed.shape[0]

        if length_difference > 0:
            zeros_pad = np.zeros((length_difference, self.input_size))
            return np.vstack([zeros_pad, X_seed]).reshape((self.batch_size, -1))
        else:
            return X_seed[-self.truncated_backprop_length:].reshape((self.batch_size, -1))


    def _single_pred(self):
        X_seed = tf.placeholder(
            tf.float32,
            [1, self.truncated_backprop_length * self.input_size],
            name='X_seed'
        )
        _init_state = tf.placeholder(
            tf.float32,
            [self.num_layers, 2, self.batch_size, self.state_size]
        )
        W2 = tf.placeholder(
            tf.float32,
            [self.state_size, self.output_size],
            name="W2"
        )
        b2 = tf.placeholder(
            tf.float32,
            [1, self.output_size],
            name="b2"
        )

        state_per_layer_list = tf.unstack(_init_state, axis=0)
        rnn_tuple_state = tuple(
            [tf.nn.rnn_cell.LSTMStateTuple(state_per_layer_list[idx][0,:,:], state_per_layer_list[idx][1,:,:])
            for idx in range(self.num_layers)]
        )

        stacked_rnn = []
        for _ in range(self.num_layers):
            stacked_rnn.append(tf.nn.rnn_cell.LSTMCell(
                self.state_size, state_is_tuple=True, reuse=tf.get_variable_scope().reuse
            ))
        lstm_cells = tf.nn.rnn_cell.MultiRNNCell(
            stacked_rnn,
            state_is_tuple=True
        )
        states_series, current_state = tf.nn.dynamic_rnn(
            lstm_cells,
            tf.expand_dims(X_seed, -1),
            initial_state=rnn_tuple_state
        )
        states_series = tf.reshape(states_series, [-1, self.state_size])
        # import pdb; pdb.set_trace()
        logits = tf.matmul(states_series, W2) + b2

        logits = tf.reshape(
            logits,
            [1, self.input_size * self.truncated_backprop_length, self.input_size],
        )

        logits_series = tf.unstack(logits, axis=1)
        predictions_series = [
            tf.nn.sigmoid(logits) for logits in logits_series
        ]
        return X_seed, W2, b2, _init_state, current_state, predictions_series

    def predict(self, X_seed_np, steps=40, restore_saved=True):

        # tf.reset_default_graph()
        # FIXME: THIS IS NOT RESTORING CORRECTLY!
        X_seed, W2, b2, _init_state, current_state, predictions_series = self._single_pred()

        # lstm_cells = tf.get_variable("lstm_cells")
        # W2 = tf.get_variable("W2", shape=[self.state_size, self.input_size])
        # b2 = tf.get_variable("b2", shape=[1, self.input_size])
        _W2, _b2, _current_state = self._load_model_params()
        # _current_state = np.array([[t for t in st] for st in _current_state])
        results = list()

        with tf.Session() as sess:
            # Init X_seed and _current_state

            init = tf.global_variables_initializer()

            # restore_saver = tf.train.import_meta_graph(self.model_path + '.meta')
            # restore_saver.restore(sess, tf.train.latest_checkpoint(os.path.dirname(self.model_path)))
            # Restore model variables
            sess.run(init)

            for step in range(steps):
                result, _current_state = sess.run([predictions_series, current_state], feed_dict={
                    X_seed: self.truncate_music_seed(X_seed_np),
                    W2: _W2,
                    b2: _b2,
                    _init_state: _current_state
                })
                # import pdb; pdb.set_trace()
                # _current_state = np.array([[t for t in st] for st in _current_state])
                results.append(result)

        return results
