# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from scrapy import Spider
from scrapy.spiders import Rule, CrawlSpider
from scrapy.selector import Selector
from scrapy.linkextractors import LinkExtractor

import scrapy


class ImslpSpider(CrawlSpider):
    name = 'midi'
    allowed_domains = ['imslp.org']
    # Potentially add more start urls
    start_urls = [
        'http://imslp.org/index.php?title=Category:For_piano'
    ]
    rules = (
        # How to find next page links
        Rule(LinkExtractor(restrict_css='#mw-pages > div > a'), follow=True),
        # How to parse pieces of music
        Rule(LinkExtractor(restrict_css='#catcolp1-0 > ul > li > a'), callback='parse_composition'),

    )

    def _get_simple_table_element(self, upper_level_div, header_sub_text, exclude_last_char=False):
        try:
            for ele in upper_level_div:
                # There should only be one, using loop for safety
                tables = ele.findChildren('table')
                for table in tables:
                    # There should only be one, using loop for safety
                    rows = table.findChildren('tr')
                    for row in rows:
                        if header_sub_text in row.find('th').text:
                            if exclude_last_char:
                                return row.find('td').text[:-1]
                            else:
                                return row.find('td').text
        except:
            # This exception is hit if there's a missing attribute
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

    def _get_midi_file_codes(self, upper_level_div):
        codes = map(
            lambda x: x['href'].split('/')[-1],
            filter( lambda x: 'ImagefromIndex' in x['href'],
                upper_level_div
                .find_all('a', {'rel': 'nofollow', 'class': 'external text'})
            )
        )
        return codes

    def _get_file_locations(self, soup):
        """Returns data used for constructing download urls"""
        upper_level_div = (
            soup
            .find('div', {'class': 'we'})
        )
        inner_piece_divs = upper_level_div.find_all('div', {'class': 'we_file_first we_audio_top'})
        inner_piece_divs.extend(upper_level_div.find_all('div', {'class': 'we_file we_audio_top'}))
        result = []
        for div in inner_piece_divs:
            result.append(
                (
                    div
                    .find('span', {'class': 'we_file_info2'})
                    .find('span', {'class': 'hidden'})
                    .find('a')
                )['href']
            )
        return result

    def _get_download_urls(self, imslp_codes, file_data):
        code_file_pairs = zip(imslp_codes, file_data)
        download_urls = [
            'http://ks.imslp.net/files/imglnks/usimg/{file_dir}/IMSLP{code}-{filename}'.format(
                file_dir='/'.join(fp.split('/')[2:-1]),
                code=code,
                filename=fp.split('/')[-1]
            )
            for code, fp in code_file_pairs
        ]
        return download_urls

    def parse_composition(self, response):
        # Could use a different xpath selector here rather than RE
        if response.css('#tabAudio1_tab > b > a::text').re(r'Synthesized/MIDI') == []:
            # There's no tab for midi, so we don't care about it
            yield None
        else:
            soup = BeautifulSoup(response.text, 'lxml')
            tmp_dict = {
                'piece_url': response.url,
                'complete_html': soup.text,
                'genre_categories': self._get_listed_table_element(
                    soup.find_all('div', {'class': 'wp_header'}),
                    'Genre Categories', sep='; '
                ),
                'title': self._get_simple_table_element(
                    soup.find_all('div', {'class': 'wi_body'}),
                    'Work Title', exclude_last_char=True
                ),  # Some things end with a newline char
                'composer': self._get_simple_table_element(
                    soup.find_all('div', {'class': 'wi_body'}),
                    'Composer', exclude_last_char=True
                ),
                'key': self._get_simple_table_element(
                    soup.find_all('div', {'class': 'wi_body'}),
                    'Key', exclude_last_char=True
                ),
                'publication_year': self._get_simple_table_element(
                    soup.find_all('div', {'class': 'wp_header'}),
                    'First Publication', exclude_last_char=True
                ),
                'composer_time_period': self._get_simple_table_element(
                    soup.find_all('div', {'class': 'wi_body'}),
                    'Composer Time Period', exclude_last_char=True
                ),
                'piece_style': self._get_simple_table_element(
                    soup.find_all('div', {'class': 'wi_body'}),
                    'Piece Style', exclude_last_char=True
                ),
                'instrumentation': self._get_simple_table_element(
                    soup.find_all('div', {'class': 'wi_body'}),
                    'Instrumentation', exclude_last_char=True
                ),
                'imslp_codes': self._get_midi_file_codes(
                    soup
                    .find('div', {'class': 'we'})
                ),
                'file_data': self._get_file_locations(soup)
            }
            tmp_dict.update({
                'download_urls': self._get_download_urls(tmp_dict['imslp_codes'], tmp_dict['file_data'])
            })
            yield tmp_dict

    def parse_start_url(self, response):
        for composition_href in (
                response
                .css('#catcolp1-0 > ul > li > a::attr(href)')
                .extract()
            ):
            yield response.follow(composition_href, callback=self.parse_composition)
