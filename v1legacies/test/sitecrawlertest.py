import urlparse
import os.path
import sys
import datetime
import random
import logging

CURRENTDIR = os.path.dirname(__file__)
sys.path.append(os.path.join(CURRENTDIR, '..'))

from crawler import simplecrawler
from crawler import policy
from modules import storage
from analyzer import pageparser
from analyzer.extractor import Extractor
from analyzer import updatemanager
from analyzer.updatemanager import UpdateManager
import testutil

def test_extractor(**args):
    site = args['siteid']

    updatemanager.add_task(site)
    manager = UpdateManager()
    manager.run()

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    testutil.run_test(test_extractor, siteid='ftuan')

    raw_input('Press Enter to Continue...')


