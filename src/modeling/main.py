from __future__ import print_function

from keras_model import Model
from utility.s3_mongo_inter import S3MongoInterface
from utility.playback import Playback
from parsing.input_layer_extractor import InputLayerExtractor
from parsing.output_translation import OutputLayerExtractor

import datetime as dt
import matplotlib.pyplot as plt
from matplotlib.colors import PowerNorm
import numpy as np
import os
import sys

"""
Command line args:
    str (t)rain
        str model name (date will be appended)
        int number of epochs
    str (s)ynthesize
        str: model_name (without .h5 ext) to load
        int: number of beats forward to predict
        str: save_name the name to be used for saving samples without any extension
"""

BASE_OUTPUT_FOLDER = os.path.join(
    os.path.expanduser('~'),
    "workspace/music_composition/samples"
)

def load_model(model_name):
    load_filepath = "tmp/{}".format(model_name)
    return Model(
        attempt_reload=True, save_name=load_filepath, num_epochs=0
    )

def train_save_model(model_name, num_epochs):
    save_name = "tmp/{}_{}".format(
        model_name,
        dt.datetime.now().strftime("%Y-%m-%d")
    )
    # NOTE: Set model hyperparameters in keras_model.Model class
    model = Model(
        attempt_reload=False, save_name=save_name, learning_rate=0.001,
        num_epochs=num_epochs, additional_filter_song={"composer": "Beethoven, Ludwig van"}
    )
    # "composer_time_period" {"composer": "Mozart, Wolfgang Amadeus"}
    # "Baroque", "Romantic"
    # "Beethoven, Ludwig van"
    # NOTE: If a model name is re-used on the same day, the previous model will be overwritten
    # If filtering to training subset, set
    model.fit_model(save=True, save_model_hist=False, save_every=100)


def sample_model(model, beats, name):
    ile = InputLayerExtractor([], '')
    # Produce major and minor seeds
    seeds = [
        (chord_descr, ile.truncate_music_seed(
            ile.input_layer_seed_chord(chord_descr=chord_descr),
            model.input_size,
            model.batch_size,
            model.truncated_backprop_length
        ))
        for chord_descr in ('maj', 'min', 'dyn')
    ]

    for chord_descr, seed in seeds:
        # Predict
        result, logits = model.predict_output(seed, beats)
        # Image note logits and save
        fig, ax = plt.subplots(figsize=(14, 20))
        ax.imshow(
            np.asarray(logits).reshape((200, 138)),
            norm=PowerNorm(0.4)
        )
        image_path = os.path.join(
            BASE_OUTPUT_FOLDER,
            "{name}_{maj_min}.png".format(
                name=name, maj_min=chord_descr)
        )
        fig.savefig(image_path)
        # Synthesize sound and save
        ole = OutputLayerExtractor(output_logits_list=logits)
        list_of_notes = []
        if chord_descr == 'min':
            list_of_notes.extend(ile.a_min_chord)
        elif chord_descr == 'maj':
            list_of_notes.extend(ile.c_chord)
        else:
            list_of_notes.extend(ile.excitement_seed)
        # Add the predicted notes following seed
        list_of_notes.extend(ole.list_of_notes)
        wav_filepath = os.path.join(
            BASE_OUTPUT_FOLDER,
            "{name}_{maj_min}.wav".format(
                name=name, maj_min=chord_descr)
        )
        pb = Playback(list_of_notes, tempo=60)
        pb.save(wav_filepath)


if __name__ == '__main__':
    is_training = sys.argv[1][0].lower() == 't'
    is_synthesizing = sys.argv[1][0].lower() == 's'

    if is_training:
        model_name = str(sys.argv[2])
        epochs = int(sys.argv[3])

        print("Starting training...")
        train_save_model(model_name, epochs)
        print("Done")
    elif is_synthesizing:
        model_name = str(sys.argv[2])
        num_beats = int(sys.argv[3])
        save_name = str(sys.argv[4])
        print("Loading model...")
        model = load_model(model_name)
        print("Done.\nSynthesizing predictions...")
        sample_model(model, num_beats, save_name)
