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

    def download_midi(self, url):
        return BytesIO(scrapy.Request(url, 'GET').body)

    def _exe_midi_download(self, download_url):
        pass

    def _insert_download_urls(self, insert_data):
        code_file_pairs = zip(
            [code for code in insert_data['imslp_codes']],
            [fp for fp in insert_data['file_data']]
        )
        download_urls = [
            'http://ks.imslp.net/files/imglnks/usimg/{file_dir}/IMSLP{code}-{filename}'.format(
                file_dir='/'.join(fp.split('/')[2:-1]),
                code=code,
                filename=fp.split('/')[-1]
            )
            for code, fp in code_file_pairs
        ]
        insert_data['download_urls'] = download_urls

    def process_item(self, item, spider):
        insert_data = dict(item)
        # Construct midi download url and insert into dict
        self._insert_download_urls(insert_data)
        # https://imslp.org/wiki/Special:IMSLPDisclaimerAccept/335320/hfjn
        header = {
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US,en;q=0.8',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Referer': item['piece_url']
        }
        cookies = {
            'imslp_wikiLanguageSelectorLanguage': 'en',
            'imslpdisclaimeraccepted': 'yes'
        }
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
