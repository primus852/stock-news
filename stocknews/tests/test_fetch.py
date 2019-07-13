from unittest import TestCase

from stocknews import fetch
import pandas
import os


class TestReadRss(TestCase):
    def test_folder_exists(self):
        cur_dir = os.path.abspath(os.path.dirname(__file__))
        data_dir = os.path.abspath(cur_dir + "/../data/")
        self.assertTrue(os.path.exists(data_dir))

    def test_can_read(self):
        entry = fetch.read_rss(['AMAZN'], use_csv=False)
        self.assertTrue(isinstance(entry, pandas.DataFrame))
