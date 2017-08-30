# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy import log
from scrapy.conf import settings

import pymongo
import scrapy


class MongoDBPipeline(object):

    collection_name = 'scrapy_items'

    def __init__(self):
        self.client = pymongo.MongoClient(
            settings['MONGODB_SERVER'],
            settings['MONGODB_PORT']
        )
        self.db = self.client[settings['MONGODB_DB']]
        self.collection = self.db[settings['MONGODB_COLLECTION']]

    def process_item(self, item, spider):
        insert_data = dict(item)
        self.collection.insert(insert_data)
        log.msg(
            "added title/composer--{title}/{composer}".format(
                insert_data['title'], insert_data['composer']
            ),
            level=log.DEBUG, spider=spider
        )
        return item

    def close_spider(self, spider):
        self.client.close()
