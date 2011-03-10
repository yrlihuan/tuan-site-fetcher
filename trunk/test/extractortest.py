import sys
import os.path
import logging

CURRENTDIR = os.path.dirname(__file__)
ROOTDIR = os.path.join(CURRENTDIR, '..')
ANALYZERSITE = os.path.join(ROOTDIR, 'analyzer_site')
sys.path.append(CURRENTDIR)
sys.path.append(ROOTDIR)
sys.path.append(ANALYZERSITE)

import testutil
import extractor

def test_extract_site(siteid='nuomi'):
    groupons = extractor.update_site(siteid)

    props = {}
    for g in groupons:
        for prop in vars(g):
            value = getattr(g, prop)
            if value and value != '':
                if prop in props:
                    props[prop] += 1
                else:
                    props[prop] = 1

    print groupons[2].url
    print type(groupons[2].original)

    for prop in props:
        print prop + ': %d' % props[prop]


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    testutil.run_test(test_extract_site, siteid='didatuan')
    # testutil.run_test(test_update_manager)
