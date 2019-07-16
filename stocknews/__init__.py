import os
import datetime as dt
import pandas
import feedparser
import requests
import nltk
import sys
from numpy import median
from nltk.sentiment.vader import SentimentIntensityAnalyzer


class StockNews:
    YAHOO_URL = 'https://feeds.finance.yahoo.com/rss/2.0/headline?s=%s&region=US&lang=en-US'
    TRADING_URL = 'https://api.worldtradingdata.com/api/v1/history'
    DATA_FOLDER = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'data')

    def __init__(self, stocks, news_file='news.csv', summary_file='data.csv', save_news=True, closing_hour=20,
                 closing_minute=0, wt_key=None):
        """
        :param stocks: A list of Stock Symbols such as "AAPL" for Apple, NFLX for Netflix etc.
        :param news_file: Filename of saved news data
        :param summary_file: Filename of saved summary (Stock by day)
        :param save_news: Persist the data to csv or not
        :param closing_hour: attach news for the next trading day after this
        :param closing_minute: attach news for the next trading day after this
        :param wt_key: API Key from https://www.worldtradingdata.com/
        """

        self.stocks = stocks
        self.news_file = news_file
        self.summary_file = summary_file
        self.save_news = save_news
        self.closing_hour = closing_hour
        self.closing_minute = closing_minute
        self.wt_key = wt_key

        if self.save_news:
            self._touch('news')

        self._touch('summary')

    def _touch(self, df_type):
        """
        Check if folder/file exists, if not, create it
        :param df_type:
        :return:
        """

        if df_type == 'news':
            header = \
                'guid;' \
                'stock;' \
                'title;' \
                'summary;' \
                'published;' \
                'p_date;' \
                'sentiment_summary;' \
                'sentiment_title'
            file = self.news_file
        elif df_type == 'summary':
            header = \
                'id;' \
                'stock;' \
                'news_dt;' \
                'check_day;' \
                'open;' \
                'close;' \
                'high;' \
                'low;' \
                'volume;' \
                'change;' \
                'sentiment_summary_avg;' \
                'sentiment_summary_med;' \
                'sentiment_title_avg;' \
                'sentiment_title_med'
            file = self.summary_file
        else:
            raise Exception('Unknown type')

        if not os.path.exists(self.DATA_FOLDER):
            os.makedirs(self.DATA_FOLDER)

        path = os.path.join(self.DATA_FOLDER, file)

        if not os.path.isfile(path):
            with open(path, 'a') as f:
                os.utime(path, None)
                f.write(header)

    def read_rss(self):
        """
        :return: pandas.DataFrame
        """

        """Create the file"""
        if self.save_news:
            df = pandas.read_csv(os.path.join(self.DATA_FOLDER, self.news_file), header=0, sep=';')
        else:
            df = pandas.DataFrame(
                columns=['guid',
                         'stock',
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
            nltk.download('vader_lexicon', quiet=True)

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

                """Parse the date"""
                p_date = '%s_%s' % (
                    stock, dt.datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S +0000').strftime("%Y-%m-%d"))

                """Add new entry to DF"""
                row = [
                    entry.guid,
                    stock,
                    entry.title,
                    entry.summary,
                    entry.published,
                    p_date,
                    _summary,
                    _title
                ]
                df.loc[len(df)] = row

            """Save to CSV"""
            if self.save_news:
                df.to_csv(os.path.join(self.DATA_FOLDER, self.news_file), index=False, sep=';')

        return df

    def summarize(self):
        """
        Summarize news by day and get the Stock Value
        :return: pandas.DataFrame, <int> number of requests made
        """

        if self.wt_key is None:
            raise Exception('Please set the WorldTradingData API Key. '
                            'Get your key here: https://www.worldtradingdata.com')

        """Read News CSV"""
        df = self.read_rss()

        """Read Summary CSV"""
        df_sum = pandas.read_csv(os.path.join(self.DATA_FOLDER, self.summary_file), header=0, sep=';')

        """Count Requests"""
        r_count = 0

        for index, row in df.iterrows():

            """Parse the Date from CSV"""
            news_date = dt.datetime.strptime(row['published'], '%a, %d %b %Y %H:%M:%S +0000')
            check_date = self._get_check_date(news_date)

            """Create ID for summary"""
            _id = '%s_%s' % (row['stock'], news_date.strftime("%Y-%m-%d"))

            """Find id (SYMBOL_DATE) if exists, skip it"""
            sum_id = df_sum.loc[df_sum['id'] == _id]
            if len(sum_id) > 0:
                continue

            """Get all News where p_date is the sum_id"""
            _df = df[df['p_date'] == _id]

            """Make Median and AVG"""
            avg_summary, med_summary = self._median_avg('sentiment_summary', _df)
            avg_title, med_title = self._median_avg('sentiment_title', _df)

            """Add new entry to DF"""
            _row = [
                _id,
                row['stock'],
                news_date.strftime("%Y-%m-%d %H:%M:%S"),
                check_date.strftime("%Y-%m-%d"),
                0,
                0,
                0,
                0,
                0,
                'UNCHECKED',
                avg_summary,
                med_summary,
                avg_title,
                med_title
            ]
            df_sum.loc[len(df_sum)] = _row

        """Update all 'UNCHECKED' columns"""
        _df_uc = df_sum[df_sum['change'] == 'UNCHECKED']

        """Go through all unchecked"""
        for index_uc, row_uc in _df_uc.iterrows():

            """If the check_day is today, skip it"""
            _date = dt.datetime.strptime(row_uc['check_day'], '%Y-%m-%d')
            c_date = dt.datetime(_date.year, _date.month, _date.day, 23, 59, 59)
            today = dt.datetime.now()

            if c_date >= today:
                continue

            params = {
                'symbol': row_uc['stock'],
                'date_from': row_uc['check_day'],
                'date_to': row_uc['check_day'],
                'api_token': self.wt_key
            }

            r = requests.get(url=self.TRADING_URL, params=params)

            """We made a request"""
            r_count += 1

            """extracting data in json format"""
            data = r.json()

            """Extract open and close"""
            if 'history' in data.keys():

                _open = float(data['history'][row_uc['check_day']]['open'])
                _close = float(data['history'][row_uc['check_day']]['close'])
                _high = float(data['history'][row_uc['check_day']]['high'])
                _low = float(data['history'][row_uc['check_day']]['low'])
                _volume = float(data['history'][row_uc['check_day']]['volume'])

                if _open >= _close:
                    change = 'loss'
                else:
                    change = 'win'

                df_sum.loc[df_sum['id'] == row_uc['id'], 'change'] = change
                df_sum.loc[df_sum['id'] == row_uc['id'], 'open'] = _open
                df_sum.loc[df_sum['id'] == row_uc['id'], 'close'] = _close
                df_sum.loc[df_sum['id'] == row_uc['id'], 'high'] = _high
                df_sum.loc[df_sum['id'] == row_uc['id'], 'low'] = _low
                df_sum.loc[df_sum['id'] == row_uc['id'], 'volume'] = _volume

        df_sum.to_csv(os.path.join(self.DATA_FOLDER, self.summary_file), index=False, sep=';')

        return df_sum, r_count

    @staticmethod
    def _median_avg(column, t_df):
        """
        Return AVG and Median of a column
        :param column: Column Name
        :param t_df: pandas.DataFrame
        :return:
        """

        avg = t_df[column].sum() / len(t_df)
        med = median(t_df[column])

        return avg, med

    def _get_check_date(self, dt_check):
        """
        Check which day needs to be checked for a news date
        :param dt_check: datetime
        :return: dt.datetime
        """

        """Get closing date"""
        dt_close = dt.datetime(dt_check.year, dt_check.month, dt_check.day, self.closing_hour, self.closing_minute, 0)

        """If the CheckDate is later than CloseDate, add one day"""
        if dt_check > dt_close:
            dt_check += dt.timedelta(days=1)

        """If the CheckDate is a Saturday, add 2 days"""
        if dt_check.weekday() == 5:
            dt_check += dt.timedelta(days=2)

        """If the CheckDate is a Sunday, add 1 day"""
        if dt_check.weekday() == 6:
            dt_check += dt.timedelta(days=1)

        """return date to check"""
        return dt_check
