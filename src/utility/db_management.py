from __future__ import print_function

from settings import (
    BUCKET_NAME, MONGODB_SERVER, MONGODB_PORT, MONGODB_DB, MONGODB_COLLECTION,
    HEADERS, COOKIES, MIN_SLEEP, MAX_SLEEP
)

from getpass import getpass, getuser

import os
import sys

"""
Command line args:
    1: str "(r)estore" or "(d)ump"
    2: str directory path

Move the zipped database using scp
"""

def dump_database(output_dir):
    """
    Takes the current, local mongoDB specified in settings.py and dumps
    it at output_dir
    """
    print("Dumping db")
    dump_command = "mongodump --gzip --host {host} --port {port} --out {outpath} --db {db}"
    dump_command = dump_command.format(
        host="127.0.0.1",
        port=MONGODB_PORT,
        outpath=output_dir,
        db=MONGODB_DB
    )
    print(dump_command)
    os.system(dump_command)
    print("Done")

def restore_db(input_dir):
    print("Restoring db")
    restore_command = "mongorestore --gzip --nsInclude {db}.{collection} {input_dir}"
    restore_command = restore_command.format(
        db=MONGODB_DB,
        collection=MONGODB_COLLECTION,  # Also supports wildcards
        input_dir=input_dir
    )
    os.system(restore_command)
    print("Done")

if __name__ == '__main__':
    dump_bool = sys.argv[1].lower()[0] == 'd'
    restore_bool = sys.argv[1].lower()[0] == 'r'
    directory = sys.argv[2]

    if dump_bool:
        dump_database(directory)
    elif restore_bool:
        restore_db(directory)
    else:
        print("Sys args don't make sense")
