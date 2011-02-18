import urlparse
import os.path
import sys
import datetime
import random
import traceback

CURRENTDIR = os.path.dirname(__file__)
sys.path.append(os.path.join(CURRENTDIR, '..'))

from crawler import simplecrawler
from crawler import policy
from modules import storage
from analyzer import pageparser
from analyzer.extractor import Extractor
from analyzer.updatemanager import UpdateManager
import testutil

def test_extractor(**args):
    manager = UpdateManager()
    manager.run()

if __name__ == '__main__':
    testutil.run_test(test_extractor, siteid='local')

    raw_input('Press Enter to Continue...')


