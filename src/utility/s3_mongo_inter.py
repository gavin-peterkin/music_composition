from __future__ import print_function

from settings import (
    BUCKET_NAME, MONGODB_SERVER, MONGODB_PORT, MONGODB_DB, MONGODB_COLLECTION,
    HEADERS, COOKIES, MIN_SLEEP, MAX_SLEEP
)

from io import BytesIO

import boto3
import random
import requests
import time
import pymongo


class S3MongoInterface(object):

    def __init__(self, enable_frequency_checks=False):
        self.enable_frequency_checks = enable_frequency_checks

        self.s3 = boto3.resource('s3')
        self.bucket = self.s3.Bucket(BUCKET_NAME)
        # use "put_object"

        self.mongo_client = pymongo.MongoClient(MONGODB_SERVER, MONGODB_PORT)
        self.mongodb = self.mongo_client[MONGODB_DB]
        self.collection = self.mongodb[MONGODB_COLLECTION]

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

    def pull_midi_data(self, mongo_query):
        """
        Generator that yields bytestream for all midi files that are returned
        by querying DB with <mongo_query>
        """
        # self.collection.get()["Body"].read()
        pass
