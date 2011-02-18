# coding=utf-8

import sys
import os.path
import random
import re
import traceback
import logging
from datetime import datetime

CURRENTDIR = os.path.dirname(__file__)
sys.path.append(os.path.join(CURRENTDIR, '..'))

from modules.BeautifulSoup import BeautifulSoup
from modules import storage
from crawler.simplecrawler import SimpleCrawler
from crawler import policy
from analyzer.pageparser import Parser
from analyzer.pageparser import ParseResult
from analyzer.extractor import Extractor
from analyzer.tags import *

DeadlineExceededError = None
AppEngine = False
try:
    from google.appengine.runtime.apiproxy_errors import DeadlineExceededError
    AppEngine = True
except:
    class DeadlineExceededError(Exception):
        pass

MAXIMUM_PAGES_FOR_PARSER = 60
MAXIMUM_PAGES_PER_SAVE = 40

SITES_CFG = 'sites.xml'

STATE_INITIALIZING = 'initializing'
STATE_PARSING = 'parsing'
STATE_EXTRACTING = 'extracting'
STATE_FINISHED = 'finished'
STATE_ERROR = 'error'

class UpdateManager(object):

    def __init__(self, reset=False):

        self.load_site_list()

        if reset:
            self.reset()

    def run(self):
        try:
            site = self.set_working_site()
            if not site:
                return

            policy = self.loadpolicy(site)

            while True:
                state, data = self.load_state(site)
                if state == STATE_INITIALIZING:
                    nextstate = STATE_PARSING
                    self.update_state(site, nextstate)
                    continue
                elif state == STATE_PARSING:
                    self.parse(site, policy)
                    nextstate = STATE_EXTRACTING
                    self.update_state(site, nextstate)
                    continue
                elif state == STATE_EXTRACTING:
                    self.extract(site, policy, data)
                    nextstate = STATE_FINISHED
                    self.update_state(site, nextstate)
                    continue
                elif state == STATE_FINISHED or state == STATE_ERROR:
                    break
        except Exception, ex:
            if not isinstance(ex, DeadlineExceededError):
                error = traceback.format_exc()
                logging.error(error)
                nextstate = STATE_ERROR
                self.update_state(site, nextstate, error=error)


    def load_site_list(self):
        cfg = open(os.path.join(CURRENTDIR, SITES_CFG), 'r')
        soup = BeautifulSoup(cfg)

        self.sites = []
        for node in soup.findAll('site'):
            self.sites.append(node.text)

        if AppEngine and 'local' in self.sites:
            self.sites.remove('local')

        logging.info('Sites are: ' + str(self.sites))

    def loadpolicy(self, site):
        config = os.path.join(CURRENTDIR, '../crawler/configs/%s.xml' % site)
        return policy.read_config(config)

    def set_working_site(self):
        for site in self.sites:
            site_entity = storage.query(storage.SITE, siteid=site).get()
            if not site_entity:
                storage.add_or_update(storage.SITE,
                                      'siteid',
                                      siteid=site,
                                      state=STATE_INITIALIZING,
                                      lastupdate=datetime.now())

                return site
            elif site_entity.state == STATE_INITIALIZING or \
                 site_entity.state == STATE_PARSING or \
                 site_entity.state == STATE_EXTRACTING:
                return site

        return None

    def reset(self):
        storage.delete(storage.SITE)
        storage.delete(storage.PAGE)
        storage.delete(storage.PARSER)
        storage.delete(storage.GROUPON)

    def load_state(self, site):
        site_entity = storage.query(storage.SITE, siteid=site).get()
        return site_entity.state, site_entity.data

    def update_state(self, site, state, error='', data=''):
        storage.add_or_update(storage.SITE, 'siteid', siteid=site, state=state, error=error, data=data)

    def parse(self, site, policy):
        crawler = SimpleCrawler(policy)
        parser = Parser()

        pages = []
        count = 0
        for page in crawler.crawled_pages():
            pages.append(page)

            count += 1
            if count >= MAXIMUM_PAGES_FOR_PARSER:
                break

        seeds = self._generate_seeds(pages)
        parser_result = parser.probe(seeds)        

        storage.add_or_update(storage.PARSER, siteid=site, **parser_result.info_paths)
        
    def extract(self, site, policy, data):
        crawler = SimpleCrawler(policy, data)
        extractor = Extractor()
        dbparser = storage.query(storage.PARSER, siteid=site).get()
        parseresult = self._convert_to_parseresult(dbparser)

        count = 0
        products = {}
        for groupon in storage.query(storage.GROUPON, siteid=site):
            products[groupon.title] = groupon

        for page in crawler.crawled_pages():
            info = extractor.run(parseresult, page)
            if info:
                title = info[TAG_TITLE]
                if title not in products:
                    products[title] = None
                    storage.add_or_update(storage.GROUPON,
                                          siteid = site,
                                          **info)
                else:
                    if TAG_CITY in info:
                        p = products[title]
                        if not p:
                            p = storage.query(storage.GROUPON, title=title).get()
                            products[title] = p

                        city = info[TAG_CITY]
                
                        if not p.city:
                            p.city = city
                        elif city not in p.city:
                            p.city += u',' + city
                
                        p.put()

            count += 1            
            if count >= MAXIMUM_PAGES_PER_SAVE:
                data = crawler.save_crawler_state()
                self.update_state(site, STATE_EXTRACTING, data=data)
                count = 0
                continue

    def _convert_to_parseresult(self, parser):
        tags = [TAG_DISCOUNT,
                TAG_ORIGINAL,
                TAG_SAVED,
                TAG_PRICE,
                TAG_LOCATION,
                TAG_ITEMS,
                TAG_TITLE,
                TAG_IMAGE,
                TAG_CURRENCY,
                TAG_CITY,
                TAG_DETAILS,
                TAG_URL]

        parseresult = ParseResult()
        for tag in tags:
            if hasattr(parser, tag):
                value = getattr(parser, tag)
                if value and value != '':
                    parseresult.info_paths[tag] = value

        return parseresult

    def _generate_seeds(self, pages):
        seeds = []
        cnt = len(pages)
        seed_num = min(16, cnt / 5)
        seed_list = []
        for i in range(0, seed_num):
            ind = random.randint(0, cnt - 1)
            while ind in seed_list:
                ind = random.randint(0, cnt - 1)

            seed_list.append(ind)
            seeds.append(pages[ind])

        return seeds
