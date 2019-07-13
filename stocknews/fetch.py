import os
import datetime as dt
import pandas
import feedparser
import requests
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

YAHOO_URL = 'https://feeds.finance.yahoo.com/rss/2.0/headline?s=%s&region=US&lang=en-US'
TRADING_URL = 'https://api.worldtradingdata.com/api/v1/history'
DATA_FOLDER = 'data'
NASDAQ_CLOSING_HOUR = 20


def touch(file):
    """
    Check if file exists, if not, create it
    """
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)
    path = '%s/%s' % (DATA_FOLDER, file)
    if not os.path.isfile(path):
        with open(path, 'a') as file:
            os.utime(path, None)
            file.write('guid,stock,change,title,summary,published,p_date,sentiment_summary, sentiment_title')


def read_rss(stocks, use_csv=True, file='news.csv'):
    """
    :param stocks: list of stocks to check from yahoo
    :param use_csv: read/save to csv
    :param file: csv to save to
    :return: pandas.DataFrame
    """

    """Create the file"""
    if use_csv:
        touch(file)
        df = pandas.read_csv(DATA_FOLDER + '/' + file, header=0)
    else:
        df = pandas.DataFrame(
            columns=['guid', 'stock', 'change', 'title', 'summary', 'published', 'p_date', 'sentiment_summary',
                     'sentiment_title']
        )

    """Start Size of DF"""
    start_size = df.shape[0]

    """Download VADER"""
    try:
        nltk.data.find('vader_lexicon')
    except LookupError:
        nltk.download('vader_lexicon')

    for stock in stocks:

        """Init new Parser"""
        feed = feedparser.parse(YAHOO_URL % stock)

        for entry in feed.entries:

            """Find guid and skip if exists"""
            guid = df.loc[df['guid'] == entry.guid]
            if len(guid) > 0:
                continue

            """Analyze the sentiment"""
            sia = SentimentIntensityAnalyzer()
            _summary = sia.polarity_scores(entry.summary)['compound']
            _title = sia.polarity_scores(entry.title)['compound']

            """Set changed value during day. These will be updated later"""
            _change = 0

            """Parse the date"""
            p_date = '%s_%s' % (
                stock, dt.datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S +0000').strftime("%Y-%m-%d"))

            """Add new entry to DF"""
            row = [entry.guid, stock, _change, entry.title, entry.summary, entry.published, p_date, _summary, _title]
            df.loc[len(df)] = row

        """Save to CSV"""
        if use_csv:
            df.to_csv(DATA_FOLDER + '/' + file, index=False)

    end_size = df.shape[0]
    added = end_size - start_size

    print('Total News: %i (%i added last round)' % (end_size, added))

    return df


def update_stock_values(stock_symbol, file='news.csv'):
    """
    Check for zero values in opening and closing values for the past and update them
    :param stock_symbol: Symbol from NASDAQ
    :param file:
    :return:
    """
	
	if 'WORLDTRADING_KEY' not in os.environ:
		print('Please set "WORLDTRADING_KEY" in your environment variables: Get an API key at https://www.worldtradingdata.com/')
		exit()

    """Read CSV"""
    df = pandas.read_csv(DATA_FOLDER + '/' + file, header=0)

    """Temp list for checked stock/data"""
    _temp_check = []

    """Count Requests"""
    count_r = 0

    for index, row in df.iterrows():

        """Parse the Date from CSV"""
        date_time_check = dt.datetime.strptime(row['published'], '%a, %d %b %Y %H:%M:%S +0000')

        """Adjust the closing of NASDAQ (if after, the news has no influence of the news date)"""
        date_time_close = dt.datetime(date_time_check.year, date_time_check.month, date_time_check.day,
                                      NASDAQ_CLOSING_HOUR, 0, 0)

        """If it was after opening hours, select next day"""
        date_check = date_time_check
        if date_time_check > date_time_close:
            date_check = date_time_check + dt.timedelta(days=1)

        """If Date to check is saturday, add 2 days"""
        if date_check.weekday() == 5:
            date_check += dt.timedelta(days=2)
        elif date_check.weekday() == 6:
            date_check += dt.timedelta(days=1)

        """Get Yesterday"""
        yesterday = dt.datetime.now()
        yesterday -= dt.timedelta(days=1)

        """If the Date to check is later than yesterday, skip it, it will be done another day"""
        if date_check.strftime("%Y-%m-%d") > yesterday.strftime("%Y-%m-%d"):
            continue

        params = {
            'symbol': stock_symbol,
            'date_from': date_check.strftime("%Y-%m-%d"),
            'date_to': date_check.strftime("%Y-%m-%d"),
            'api_token': os.environ.get('WORLDTRADING_KEY')
        }

        _temp_key = '%s_%s' % (stock_symbol, date_check.strftime("%Y-%m-%d"))
        if _temp_key in _temp_check or row['change'] != '0':
            continue

        r = requests.get(url=TRADING_URL, params=params)

        count_r += 1

        """extracting data in json format"""
        data = r.json()

        """Extract open and close"""
        if 'history' in data.keys():

            _temp_check.append(_temp_key)

            _open = float(data['history'][date_check.strftime("%Y-%m-%d")]['open'])
            _close = float(data['history'][date_check.strftime("%Y-%m-%d")]['close'])

            if _open >= _close:
                change = 'loss'
            else:
                change = 'win'

            df.loc[df['p_date'] == _temp_key, 'change'] = change

    df.to_csv(DATA_FOLDER + '/' + file, index=False)

    return count_r
