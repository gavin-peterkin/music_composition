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



def main():
    print("Initializing connections...")
    interface = S3MongoInterface()
    print("Done.")

    # Be more selective about music that you want here:
    query = {}
    for id_, filename, midi_byte_stream, expected_key in interface.pull_midi_data(query, limit=10):

        midi_parser = MidiParser(midi_byte_stream, expected_key)

        key_signature = midi_parser.best_estimated_key_signature

        if not key_signature:
            # add that we don't know key signature to the database
            interface.collection.update_one(
                {'_id': id_},
                {"$set": {"missing_key": 1}}, upsert=False
            )
            print("Missing key_signature for file {}".format(filename))
            continue
        #
        ile = InputLayerExtractor(midi_parser.list_of_notes, key_signature)
        import pdb; pdb.set_trace()






if __name__ == '__main__':
    main()
