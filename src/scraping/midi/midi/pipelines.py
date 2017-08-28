# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html


# class MidiPipeline(object):
#     def process_item(self, item, spider):
#         return item

from io import BytesIO

import gridfs
import pymongo
import scrapy

class MongoDBPipeline(object):

    collection_name = 'scrapy_items'

    def __init__(self, mongo_uri, mongo_db):
        connection = pymongo.MongoClient(
            settings['MONGODB_SERVER'],
            settings['MONGODB_PORT']
        )
        db = connection[settings['MONGODB_DB']]
        self.collection = db[settings['MONGODB_COLLECTION']]
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    def download_midi(self, url):
        return BytesIO(scrapy.Request(url, 'GET').body)

    def process_item(self, item, spider):
        insert_data = dict(item)
        insert_data.update({'midi_files': [
            self.download_midi(url) for url in item['download_midi_urls']
        ]})
        self.collection.insert(insert_data)
        log.msg(
            "added title/composer--{title}/{composer}".format(
                item['title'], item['composer']
            ),
            level=log.DEBUG, spider=spider
        )
        return item

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'items')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()
