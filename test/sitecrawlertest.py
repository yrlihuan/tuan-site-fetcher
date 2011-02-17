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
import testutil

def test_extractor(**args):
    site = args['siteid']
    config = os.path.join(CURRENTDIR, '..\\crawler\\configs\\%s.xml' % site)
    p = policy.read_config(config)

    extractor = Extractor(p, storage)
    extractor.run()

def test_site(**args):
    site = args['siteid']

    config = os.path.join(CURRENTDIR, '..\\crawler\\configs\\%s.xml' % site)
    p = policy.read_config(config)

    all_urls = []
    if 'refresh' in args and args['refresh']:
        # clean all the pre storaged data
        storage.delete(storage.SITE, siteid=p.site)
        storage.delete(storage.PAGE, siteid=p.site)
        storage.delete(storage.PARSER, siteid=p.site)

        sites = storage.query(storage.SITE, siteid=p.site)
        pages = storage.query(storage.PAGE, siteid=p.site)
        parsers = storage.query(storage.PARSER, siteid=p.site)

        testutil.assert_eq(len(tolist(sites)), 0)
        testutil.assert_eq(len(tolist(pages)), 0)
        testutil.assert_eq(len(tolist(pages)), 0)
        testutil.assert_eq(len(tolist(parsers)), 0)

        # crawling...
        storage.add_or_update(storage.SITE,
                              'siteid',
                              siteid = p.site)

        crawler = simplecrawler.SimpleCrawler(p)
        for page in crawler.crawled_pages():
            print page.url
            all_urls.append(page.url)
            storage.add_or_update(storage.PAGE,
                                  'url',
                                  siteid = p.site,
                                  url = page.url,
                                  data = page.content,
                                  updatedate=datetime.datetime.now(),
                                  infopage = False,
                                  linktext = page.linktext)

    # generate seeds for analysis
    seeds = []
    cnt = len(all_urls)
    if cnt > 50:
        seed_num = min(10, cnt / 5)
        for i in range(0, seed_num):
            ind = random.randint(0, cnt - 1)
            page = iter(storage.query(storage.PAGE, siteid=p.site, url=all_urls[ind])).next()

            seeds.append(page)

    # analyzing...
    ana = pageparser.Parser()
    pages = storage.query(storage.PAGE, siteid=p.site).fetch(1000)

    results = ana.run_batch(pages, seeds)
    unique_results = {}

    for ind, r in enumerate(results):
        if not r:
            parserid = -1
        elif r in unique_results:
            parserid = unique_results[r]
        else:
            # generate unique id
            uniqueid = 0
            while True:
                uniqueid = random.randint(0, 1<<30)

                if not storage.query(storage.PARSER, parserid=uniqueid).get():
                    break

            # add the result to parser table
            properties = dict(r.info_paths)
            properties['parserid'] = uniqueid
            properties['siteid'] = p.site
            storage.add_or_update(storage.PARSER, 'parserid', **properties)

            parserid = uniqueid
            unique_results[r] = uniqueid

        storage.add_or_update(storage.PAGE, 'url', url=pages[ind].url, parserid=parserid)

def tolist(iterable):
    r = []
    for i in iterable:
        r.append(i)

    return r

if __name__ == '__main__':
    # testutil.run_test(test_site, siteid='ayatuan', refresh=True)
    testutil.run_test(test_extractor, siteid='ayatuan')

    raw_input('Press Enter to Continue...')


