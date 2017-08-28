# -*- coding: utf-8 -*-
from scrapy import Spider
from scrapy.selector import Selector
from scrapy.linkextractors import LinkExtractor

import scrapy

selection_dictionary = {
    'genre_categories': '//*[@id="wiki-body"]/div[@class="body"]/div[@class="mw-content-ltr"]/div[@class="wp_header"]/table/tbody/tr/'
}


class ImslpSpider(Spider):
    name = 'imslp'
    allowed_domains = ['imslp.org']
    # Potentially add more start urls
    start_urls = [
        'http://imslp.org/index.php?title=Category:For_piano'
    ]

    def _get_simple_table_element(self, upper_level_div, header_sub_text):
        for ele in upper_level_div:
            # There should only be one, using loop for safety
            tables = ele.findChildren('table')
            for table in tables:
                # There should only be one, using loop for safety
                rows = table.findChildren('tr')
                for row in rows:
                    if header_sub_text in row.find('th').text:
                        return row.find('td').text
        return None

    def _get_listed_table_element(self, upper_level_div, header_sub_text, sep='; '):
        for ele in upper_level_div:
            # There should only be one, using loop for safety
            tables = ele.findChildren('table')
            for table in tables:
                # There should only be one, using loop for safety
                rows = table.findChildren('tr')
                for row in rows:
                    if header_sub_text in row.find('th').text:
                        return row.find('td').text.split(sep)
        return None

    def _get_midi_urls(self, upper_level_div):
        codes = map(
            lambda x: x['href'].split('/')[-1],
            filter( lambda x: 'ImagefromIndex' in x['href'],
                upper_level_div
                .find_all('a', {'rel': 'nofollow', 'class': 'external text'})
            )
        )
        # This let's us bypass an additional page
        return [
            'https://imslp.org/wiki/Special:IMSLPDisclaimerAccept/{code_}/hfjn'.format(code_=code)
            for code in codes
        ]

    def parse_composition(self, response):
        # Yields item information
        response = scrapy.Request(piece_page)
        # Could use a different xpath selector here rather than RE
        if response.css('#tabAudio1_tab > b > a::text').re(r'Synthesized/MIDI') == []:
            # There's no tab for midi, so we don't care about it
            pass
        else:
            soup = BeautifulSoup(response.text, 'lxml')
            yield {
                'piece_url': response.url,
                'complete_html': soup.text,
                'genre_categories': self._get_listed_table_element(
                    soup.find_all('div', class_='wp_header'),
                    'Genre Categories', sep='; '
                ),
                'title': self._get_table_element(
                    soup.find_all('div', class_'wi_body'),
                    'Work Title'
                )[:-1],  # Some things end with a newline char
                'composer': self._get_table_element(
                    soup.find_all('div', class_='wi_body'),
                    'Composer'
                )[:-1],
                'key': self._get_table_element(
                    soup.find_all('div', class_'wi_body'),
                    'Key'
                )[:-1],
                'publication_year': self._get_table_element(
                    soup.find_all('div', class_='wp_header'),
                    'First Publication'
                )[:-1],
                'composer_time_period': self._get_table_element(
                    soup.find_all('div', class_='wi_body'),
                    'Composer Time Period'
                ),
                'piece_style': self._get_table_element(
                    soup.find_all('div', class_='wi_body'),
                    'Piece Style'
                ),
                'instrumentation': self._get_table_element(
                    soup.find_all('div', class_='wi_body'),
                    'Instrumentation'
                )[:-1],
                'download_urls': self._get_midi_urls(
                    soup
                    .find('div', {'class': 'we'})
                )

            }

    https://imslp.org/wiki/Special:IMSLPDisclaimerAccept/220145/hfjn
    https://imslp.org/wiki/Special:IMSLPDisclaimerAccept/220146/hfjn


    def parse(self, response):
        for composition_href in (
            Selector(response)
            .css('#catcolp1-0 > ul > li > a::attr(href)')
            .extract()
        ):
            yield response.follow(composition_href, self.parse_composition)

        for new_page_href in (
            response
            .css('#mw-pages > div > a::attr(href)')
            .extract_first()
        ):
            yield response.follow(new_page_href, self.parse)
