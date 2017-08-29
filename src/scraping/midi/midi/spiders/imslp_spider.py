# -*- coding: utf-8 -*-
from scrapy import Spider
from scrapy.selector import Selector
from scrapy.linkextractors import LinkExtractor

import scrapy


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

    def _get_midi_file_codes(self, upper_level_div):
        codes = map(
            lambda x: x['href'].split('/')[-1],
            filter( lambda x: 'ImagefromIndex' in x['href'],
                upper_level_div
                .find_all('a', {'rel': 'nofollow', 'class': 'external text'})
            )
        )
        # This let's us bypass an additional confirmation page
        # https://imslp.org/wiki/Special:ImagefromIndex/220158/hfjn
        # https://imslp.org/wiki/Special:IMSLPDisclaimerAccept/220158/hfjn
        return codes
        # return [
        #     'https://imslp.org/wiki/Special:IMSLPDisclaimerAccept/{code_}/hfjn'.format(code_=code)
        #     for code in codes
        # ]

    def _get_file_locations(self, soup):
        # //*[@id="IMSLP335320"]/div[1]/p/span/span[1]/a
        # //*[@id="IMSLP220145"]/div[1]/p/span/a
        # //*[@id="IMSLP220146"]/div[1]/p/span/a
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
                'imslp_codes': self._get_midi_urls(
                    soup
                    .find('div', {'class': 'we'})
                ),
                'file_data': self_get_file_data(soup)
            }

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
