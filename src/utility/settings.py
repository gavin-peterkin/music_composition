
# Assumes AWS credentials are already set up in your environment

# Bucket name
BUCKET_NAME = 'gtp.midi.files'  # This is private

# Frequency of mongoDB checks
# Checks the database every X seconds for new urls to download
# DOWNLOAD_CHECK_FREQUENCY = 60


# Information about local mongodb
MONGODB_SERVER = "localhost"
MONGODB_PORT = 27017
MONGODB_DB = "imslp"
MONGODB_COLLECTION = "piano_pieces"

# Download request headers and cookies
HEADERS = {
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.8',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Connection': 'keep-alive',
    # 'Referer': insert_data['piece_url']
}
COOKIES = {
    'imslp_wikiLanguageSelectorLanguage': 'en',
    'imslpdisclaimeraccepted': 'yes'
}
# sleep and random number of seconds between downloads to respect IMSLP
MIN_SLEEP = 3
MAX_SLEEP = 15
