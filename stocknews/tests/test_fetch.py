from unittest import TestCase
import pandas as pd
from stocknews import StockNews


class TestReadRss(TestCase):
    def test_read_rss(self):
        sn = StockNews(['AAPL'])
        df = sn.read_rss()
        self.assertTrue(isinstance(df, pd.DataFrame))
