# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field

import scrapy


class IMSLPMidiItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    piece_url = Field()
    genre_categories = Field()
    title = Field()
    composer = Field()
    key = Field()
    publication_year = Field()
    composer_time_period = Field()
    piece_style = Field()
    instrumentation = Field()
    imslp_codes = Field()
    file_data = Field()
