import os
import datetime as dt
import pandas
import feedparser
import requests
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer


class StockNews:

    YAHOO_URL = 'https://feeds.finance.yahoo.com/rss/2.0/headline?s=%s&region=US&lang=en-US'
    TRADING_URL = 'https://api.worldtradingdata.com/api/v1/history'
    DATA_FOLDER = 'data'

    def __init__(self, stocks, file='data.csv', use_csv=True, closing_hour=20, closing_minute=0, wt_key=None):
        """
        :param stocks: A list of Stock Symbols such as "AAPL" for Apple, NFLX for Netflix etc.
        :param file: Filename of saved data
        :param use_csv: Persist the data to csv or not
        :param closing_hour: attach news for the next trading day after this
        :param closing_minute: attach news for the next trading day after this
        :param wt_key: API Key from https://www.worldtradingdata.com/
        """

        self.stocks = stocks
        self.file = file
        self.use_csv = use_csv
        self.closing_hour = closing_hour
        self.closing_minute = closing_minute
        self.wt_key = wt_key

        if self.use_csv:
            self._touch()

    def _touch(self):
        """
        Check if folder/file exists, if not, create it
        :return:
        """

        if not os.path.exists(self.DATA_FOLDER):
            os.makedirs(self.DATA_FOLDER)

        path = '%s/%s' % (self.DATA_FOLDER, self.file)

        if not os.path.isfile(path):
            with open(path, 'a') as file:
                os.utime(path, None)
                file.write(
                    'guid,'
                    'stock,'
                    'change,'
                    'open,'
                    'close,'
                    'title,'
                    'summary,'
                    'published,'
                    'p_date,'
                    'sentiment_summary,'
                    'sentiment_title'
                )

    def read_rss(self):
        """
        :param stocks: list of stocks to check from yahoo
        :return: pandas.DataFrame
        """

        """Create the file"""
        if self.use_csv:
            self._touch()
            df = pandas.read_csv(self.DATA_FOLDER + '/' + self.file, header=0)
        else:
            df = pandas.DataFrame(
                columns=['guid',
                         'stock',
                         'change',
                         'open',
                         'close',
                         'title',
                         'summary',
                         'published',
                         'p_date',
                         'sentiment_summary',
                         'sentiment_title']
            )

        """Download VADER"""
        try:
            nltk.data.find('vader_lexicon')
        except LookupError:
            nltk.download('vader_lexicon')

        for stock in self.stocks:

            """Init new Parser"""
            feed = feedparser.parse(self.YAHOO_URL % stock)

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
                _open = 0
                _close = 0

                """Parse the date"""
                p_date = '%s_%s' % (
                    stock, dt.datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S +0000').strftime("%Y-%m-%d"))

                """Add new entry to DF"""
                row = [
                    entry.guid,
                    stock,
                    _change,
                    _open,
                    _close,
                    entry.title,
                    entry.summary,
                    entry.published,
                    p_date,
                    _summary,
                    _title
                ]
                df.loc[len(df)] = row

            """Save to CSV"""
            if self.use_csv:
                df.to_csv(self.DATA_FOLDER + '/' + self.file, index=False)

        return df

    def update_stock(self, stock_symbol):
        """
        Update all the rows if use_csv=True
        :param stock_symbol: Single Stock Symbol
        :return: pandas.DataFrame
        """

        if not self.use_csv:
            raise Exception('Can only be used with when "use_csv" is set to True')

        if self.wt_key is None:
            raise Exception('Please set the WorldTradingData API Key. '
                            'Get your key here: https://www.worldtradingdata.com')

        """Read CSV"""
        df = pandas.read_csv(self.DATA_FOLDER + '/' + self.file, header=0)

        """Temp list for checked stock/data"""
        _temp_check = []

        for index, row in df.iterrows():

            """Parse the Date from CSV"""
            date_time_check = dt.datetime.strptime(row['published'], '%a, %d %b %Y %H:%M:%S +0000')

            """Adjust the closing hours (if after, the news has no influence of the news date)"""
            date_time_close = dt.datetime(date_time_check.year, date_time_check.month, date_time_check.day,
                                          self.closing_hour, self.closing_minute, 0)

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
                'api_token': self.wt_key
            }

            _temp_key = '%s_%s' % (stock_symbol, date_check.strftime("%Y-%m-%d"))
            if _temp_key in _temp_check or (row['change'] != '0' and row['change'] != 0):
                continue

            r = requests.get(url=self.TRADING_URL, params=params)

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
                df.loc[df['p_date'] == _temp_key, 'open'] = _open
                df.loc[df['p_date'] == _temp_key, 'close'] = _close

        df.to_csv(self.DATA_FOLDER + '/' + self.file, index=False)

        return df
