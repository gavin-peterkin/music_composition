from __future__ import print_function

from utility.s3_mongo_inter import S3MongoInterface

"""
Placeholder for later expansion of s3_mongo_inter

run: python main.py
"""

if __name__ == '__main__':
    print("Initializing database and s3 connections...")
    # Update interface settings in setting.py
    interface = S3MongoInterface()
    print("Done.\nDownloading and saving midi files to S3 bucket...")
    interface.execute_midi_dumps()
    print("Done.")
