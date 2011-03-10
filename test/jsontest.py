import sys
import os.path
import logging
import json

CURRENTDIR = os.path.dirname(__file__)
ROOTDIR = os.path.join(CURRENTDIR, '..')
ANALYZERSITE = os.path.join(ROOTDIR, 'analyzer_site')
sys.path.append(CURRENTDIR)
sys.path.append(ROOTDIR)
sys.path.append(ANALYZERSITE)

import testutil
import extractor

def test_json():
    logging.info(json.dumps({'2':1}))
    

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    testutil.run_test(test_json)

    raw_input('Press Enter to Continue...')

