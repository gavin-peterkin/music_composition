from __future__ import print_function

from utility.s3_mongo_inter import S3MongoInterface
from midi_parser import MidiParser

"""
Placeholder for midi parsing script that takes a list of keys corresponding
to midi files in the S3 bucket loads the file, parses it using MidiParser
and saves the resulting unicode text file in S3 while also updating the MongoDB
link attributes.

See the ipynb for detangling the mess that is midi.
"""

if __name__ == '__main__':
    print("Initializing connections...")
    interface = S3MongoInterface()
    print("Done.")
