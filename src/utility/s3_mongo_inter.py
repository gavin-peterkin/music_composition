from __future__ import print_function

from settings import (
    BUCKET_NAME, MONGODB_SERVER, MONGODB_PORT, MONGODB_DB, MONGODB_COLLECTION,
    HEADERS, COOKIES, MIN_SLEEP, MAX_SLEEP
)

from bson.binary import Binary
from io import BytesIO

import boto3
import cPickle as pickle
import random
import requests
import time
import pymongo


class S3MongoInterface(object):

    def __init__(self, enable_frequency_checks=False, enable_s3_conn=True):
        self.enable_frequency_checks = enable_frequency_checks

        # use "put_object"

        self.mongo_client = pymongo.MongoClient(MONGODB_SERVER, MONGODB_PORT)
        self.mongodb = self.mongo_client[MONGODB_DB]
        self.collection = self.mongodb[MONGODB_COLLECTION]
        self.cursor = None

        self.s3 = boto3.resource('s3')
        self.bucket = self.s3.Bucket(BUCKET_NAME)
        self.already_downloaded_keys = [obj.key for obj in self.bucket.objects.all()]

    def _execute_download(self, url):
        """Returns raw bytestream from url"""
        time.sleep(random.randint(MIN_SLEEP, MAX_SLEEP))
        response = requests.get(url)
        if response.ok:
            return BytesIO(response.content)
        else:
            return None

    def _construct_obj_key(self, url):
        """Just using the filename for now"""
        return url.split('/')[-1]

    def _insert_new_midi(self, _id, download_url):
        object_key = self._construct_obj_key(download_url)
        if object_key in self.already_downloaded_keys:
            print("Skipping already downloaded {}".format(object_key))
        else:
            data = self._execute_download(download_url)
            if data:
                self.bucket.put_object(Key=object_key, Body=data)
                self.collection.update_one(
                    {'_id': _id},
                    {"$set": {'s3_complete': 1, 's3_filename': object_key}}, upsert=False
                )
                print("Dumped file: {}".format(object_key))


    def execute_midi_dumps(self):
        """
        Looks at local MongoDB and checks for midi download urls every X seconds
        if enable_frequency_checks is True, otherwise it just checks once.

        Downloads file into memory and sends to S3 bucket with key equal to the
        original download URL.

        Upon successful completion, adds boolean document attribute "s3_complete"
        with value true and string attribute "s3_filename" that has the filename
        in the bucket.
        """
        # Get all docs with at least one midi file
        cursor = self.collection.find(
            {"download_urls": {'$elemMatch': {'$regex': '.*\.mid'}}},
            {"_id": 1, "download_urls": 1}
        )
        for doc in cursor:
            for download_url in doc['download_urls']:
                if download_url[-4:] == '.mid':
                    self._insert_new_midi(doc['_id'], download_url)

    def pull_midi_data(self, mongo_query, limit=None):
        """
        Generator that yields bytestream for all midi files that are returned
        by querying DB with <mongo_query>

        Limit: None by default. If int, returns only first int items.
        """
        # We only ever care about entries with a midi file associated with them
        # We also want to be sure to only get data that has been downloaded and
        # added to the S3 bucket
        mongo_query.update({
            "download_urls": {'$elemMatch': {'$regex': '.*\.mid'}},
            "s3_complete": 1,
            "missing_key": {"$exists": 0},
            # "has_input_layer": {"$exists": 0}  # Doesn't already have saved input layer
        })
        cursor = self.collection.find(
            mongo_query,
            {"_id": 1, "download_urls": 1, "key": 1}
        )
        i = 0
        for doc in cursor:
            web_suggested_key = doc['key']
            for download_url in doc['download_urls']:
                imslp_filename = self._construct_obj_key(download_url)
                if download_url[-4:] == '.mid':
                    i += 1
                    # yields id_, filename, data, key_sig_from_site
                    yield (
                        doc['_id'],
                        imslp_filename,
                        self.bucket.Object(key=imslp_filename).get()['Body'].read(),
                        web_suggested_key
                    )
                if limit and i >= limit:
                    break

    def insert_input_array(self, id_, arr):
        try:
            self.collection.update_one(
                {"_id": id_},
                {"$set": {
                    "input_layer_array": Binary(pickle.dumps(arr, protocol=2)),
                    "has_input_layer": 1
                }}
            )
        except pymongo.errors.DocumentTooLarge:
            self.collection.update_one(
                {"_id": id_},
                {"$set": {
                    "has_input_layer": 0
                }}
            )

    def get_input_arrays(self, mongo_query, go_forever=True):
        """
        Generator that yields an input array
        """
        mongo_query.update({
            "download_urls": {'$elemMatch': {'$regex': '.*\.mid'}},
            "has_input_layer": 1
        })
        while True:
            if self.cursor is not None:
                self.cursor.close()
            self.cursor = self.collection.find(
                mongo_query,
                {"input_layer_array": 1},
                no_cursor_timeout=True
            )
            for doc in self.cursor:
                yield pickle.loads(doc["input_layer_array"])

    def close_connections(self):
        if self.cursor is not None:
            self.cursor.close()
