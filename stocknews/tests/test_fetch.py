from unittest import TestCase
import os


class TestReadRss(TestCase):
    def test_folder_exists(self):
        cur_dir = os.path.abspath(os.path.dirname(__file__))
        data_dir = os.path.abspath(cur_dir + "/../data/")
        self.assertTrue(os.path.exists(data_dir))
