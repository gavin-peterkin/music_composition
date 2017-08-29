def _exe_midi_download(self, insert_data):
    # FIXME: remove hardcoded headers and cookies
    headers = {
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-US,en;q=0.8',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Connection': 'keep-alive',
        'Referer': insert_data['piece_url']
    }
    cookies = {
        'imslp_wikiLanguageSelectorLanguage': 'en',
        'imslpdisclaimeraccepted': 'yes'
    }
    data = []
    for url in insert_data['download_urls']:
        # FIXME: get rid of hardcoded sleep
        time.sleep(random.randint(5, 20))
        data.append(BytesIO(scrapy.Request(url, 'GET', headers=headers, cookies=cookies).body))
    insert_data['midi_files'] = data
