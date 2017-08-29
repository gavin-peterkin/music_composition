from __future__ import print_function

from pymongo import MongoClient
from settings import MONGODB_SERVER, MONGODB_PORT, MONGODB_DB, MONGODB_COLLECTION

import sys

"""
Use this file to completely drop a database and re-intialize an empty one
"""


def remove_old_db(client):
    print("Deleting entire database {}".format(MONGODB_DB))
    # to reduce the probability of an accidental db drop
    response = raw_input("Enter the number 8675309: ")
    if int(response) != 8675309:
        sys.exit("Aborting")
    client.drop_database(MONGODB_DB)

def start_up_new_db(client):
    db = client[MONGODB_DB]
    coll = db[MONGODB_COLLECTION]

if __name__ == '__main__':
    # Connect to the hosted MongoDB instance
    client = MongoClient(
        'mongodb://{server}:{port}/'.format(
            server=MONGODB_SERVER, port=MONGODB_PORT
        )
    )
    remove_old_db(client)
    start_up_new_db(client)
