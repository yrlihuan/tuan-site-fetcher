# coding=utf-8

import sys
import os.path
import random
import re
import traceback
import logging
import time
from datetime import datetime

CURRENTDIR = os.path.dirname(__file__)
sys.path.append(os.path.join(CURRENTDIR, '..'))

from modules import storage
from modules.storage import Site
from modules.BeautifulSoup import BeautifulSoup
from crawler.simplecrawler import SimpleCrawler
from crawler import policy
from analyzer.pageparser import Parser
from analyzer.pageparser import ParseResult
from analyzer.extractor import Extractor
from analyzer.tags import *

EXPORTS = 'add_task'

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

# rpc call handler
# the remote admin server calls this method to dispatch a task onto this server
def add_task(site):
    site_entity = storage.query(storage.SITE, siteid=site).get()
    if not site_entity:
        storage.add_or_update(storage.SITE,
                              'siteid',
                              siteid=site,
                              state=Site.STATE_INITIALIZING,
                              lastupdate=datetime.now())

class UpdateManager(object):
    def __init__(self, reset=False):
        if reset:
            self.reset()

        self.workerid = self._generate_id()

    def run(self):
        try:
            site = self.set_working_site()
            if not site:
                return

            policy = self.loadpolicy(site)

            while True:
                state, data = self.load_state(site)
                if state == Site.STATE_INITIALIZING:
                    nextstate = Site.STATE_PARSING
                    self.update_state(site, nextstate)
                    continue
                elif state == Site.STATE_PARSING:
                    if self.parse(site, policy):
                        nextstate = Site.STATE_EXTRACTING
                        error = ''
                    else:
                        nextstate = Site.STATE_ERROR
                        error = 'Failed to parse groupon pages structure'

                    self.update_state(site, nextstate, error=error)
                    continue
                elif state == Site.STATE_EXTRACTING:
                    self.extract(site, policy, data)
                    nextstate = Site.STATE_FINISHED
                    self.update_state(site, nextstate)
                    continue
                elif state == Site.STATE_FINISHED or state == Site.STATE_ERROR:
                    break
        except Exception, ex:
            if not isinstance(ex, DeadlineExceededError):
                error = traceback.format_exc()
                logging.error(error)
                nextstate = Site.STATE_ERROR
                self.update_state(site, nextstate, error=error)
            else:
                # this task is about to be shut down by GAE. do some clean work
                logging.info('Caught DeadlineExceededError, about to stop execution!')
                logging.info('The task started from %s, ended at %s', (time.ctime(self.workerid), time.ctime()))

    def loadpolicy(self, site):
        config = os.path.join(CURRENTDIR, '../crawler/configs/%s.xml' % site)
        return policy.read_config(config)

    def set_working_site(self):
        for site_entity in storage.query(storage.SITE):
            if Site.isrunning(site_entity.state):
                # the workerid is set to the point where the last execution is started.
                # if the new value - the old value < 60 * 10 (10mins), then there's
                # another worker thread running this task.
                old_workerid = site_entity.workerid or 0.0

                if old_workerid == 0 or self.workerid - old_workerid > 10 * 60:
                    site_entity.workerid = self.workerid
                    site_entity.put()
                    logging.info('Permission of task execution acquired! Old worker: %f, new worker: %f', old_workerid, self.workerid)
                    return site_entity.siteid
                else:
                    logging.info('Give up task execution. Old worker: %f, new worker: %f', old_workerid, self.workerid)
                    return None

        return None

    def reset(self):
        storage.delete(storage.SITE)
        storage.delete(storage.PAGE)
        storage.delete(storage.PARSER)
        storage.delete(storage.GROUPON)

    def load_state(self, site):
        site_entity = storage.query(storage.SITE, siteid=site).get()
        return site_entity.state, site_entity.data

    def update_state(self, site, state, groupon_count=-1, error='', data=''):
        params = {}
        if groupon_count >= 0:
            params['groupon_count'] = groupon_count

        site_entity = storage.query(storage.SITE, siteid=site).get()

        # if the site object in storage is missing. we do nothing
        # this could happen if the datastore is cleared by admin
        if not site_entity:
            return

        storage.add_or_update(storage.SITE, 'siteid', siteid=site, state=state, error=error, data=data, **params)

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

        if parser_result and parser_result.info_paths:
            storage.add_or_update(storage.PARSER, siteid=site, **parser_result.info_paths)
            return True
        else:
            return False
        
    def extract(self, site, policy, data):
        crawler = SimpleCrawler(policy, data)
        extractor = Extractor()
        dbparser = storage.query(storage.PARSER, siteid=site).get()
        parseresult = self._convert_to_parseresult(dbparser)

        count = 0
        products = {}
        groupon_count = 0
        for groupon in storage.query(storage.GROUPON, siteid=site):
            products[groupon.title] = groupon
            groupon_count += 1

        for page in crawler.crawled_pages():
            logging.info('UpdateManager.extract: extract from page %s' % page.url)
            info = extractor.run(parseresult, page)
            if info:
                title = info[TAG_TITLE]
                if title not in products:
                    products[title] = storage.add_or_update(storage.GROUPON,
                                                            siteid = site,
                                                            **info)
                    groupon_count += 1
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
                self.update_state(site, Site.STATE_EXTRACTING, groupon_count=groupon_count, data=data)
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
        seed_num = min(16, cnt)

        # if count of all pages is less than a certain level
        # instead of using a randomized algorithm, we just pick the last seed_num pages
        if cnt - seed_num < 5:
            return pages[cnt-seed_num:]

        seed_list = []
        for i in range(0, seed_num):
            ind = random.randint(0, cnt - 1)
            while ind in seed_list:
                ind = random.randint(0, cnt - 1)

            seed_list.append(ind)
            seeds.append(pages[ind])

        return seeds

    def _generate_id(self):
        return time.time()

