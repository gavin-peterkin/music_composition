from __future__ import print_function

from utility.s3_mongo_inter import S3MongoInterface
from utility.playback import Playback
from midi_parser import MidiParser
from input_layer_extractor import InputLayerExtractor

import sys

"""
NOTE: Ensure all midi files are downloaded and dumped into S3 bucket
prior to parsing.

Placeholder for midi parsing script that takes a list of keys corresponding
to midi files in the S3 bucket loads the file, parses it using MidiParser
and saves the resulting unicode text file in the db while also updating the MongoDB
link attributes.

See the ipynb for detangling the mess that is midi.
"""



def initialize_input_arrays():
    print("Initializing connections...")
    interface = S3MongoInterface()
    print("Done.")

    # Be more selective about music that you want to parse here:
    query = {
        "bad_file": {"$exists": 0},
        "missing_key": {"$exists": 0},
        "composer_time_period": "Classical"
    }
    for id_, filename, midi_byte_stream, expected_key in interface.pull_midi_data(query, limit=10):

        try:
            midi_parser = MidiParser(midi_byte_stream, expected_key)
        except:
            print("Bad file {}".format(filename))
            interface.collection.update_one(
                {'_id': id_},
                {"$set": {"bad_file": 1}}, upsert=False
            )
            continue

        key_signature = midi_parser.best_estimated_key_signature

        if not key_signature:
            # add that we don't know key signature to the database
            interface.collection.update_one(
                {'_id': id_},
                {"$set": {"missing_key": 1}}, upsert=False
            )
            print("Missing key_signature for file {}".format(filename))
            continue

        ile = InputLayerExtractor(
            midi_parser.list_of_notes, key_signature, center_output=True
        )
        # import pdb; pdb.set_trace()
        # Save the input layer array as binary in mongodb
        interface.insert_input_array(id_, ile.input_layer_array)
        # Print "." for progress
        sys.stdout.write('.')
        sys.stdout.flush()
    print("Done.")


if __name__ == '__main__':
    if sys.argv[1].lower() == "init":
        initialize_input_arrays()
