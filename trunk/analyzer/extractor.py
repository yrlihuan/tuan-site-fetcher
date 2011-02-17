# coding=utf-8

import sys
import os.path
import random
import re

CURRENTDIR = os.path.dirname(__file__)
sys.path.append(os.path.join(CURRENTDIR, '..'))

from modules import BeautifulSoup
from analyzer import pageparser
from crawler import simplecrawler
from analyzer.tags import *

MAXIMUM_PRE_FETCHES = 200
CITIES_CONFIG = 'cities.xml'
DIGITS_PATTERN = re.compile(u'\d+(\.\d+)?')
DEFAULT_CITY = u'北京'

class Extractor(object):
    def __init__(self, policy, storage, clear=True):
        self.policy = policy
        self.storage = storage
        self.site = policy.site
        self.parser = pageparser.Parser()

        self._init_cities()

        if clear:
            self.storage.delete(storage.PAGE, siteid=self.site)
            self.storage.delete(storage.PARSER, siteid=self.site)
            self.storage.delete(storage.GROUPON, siteid=self.site)
    
    def run(self):
        crawler = simplecrawler.SimpleCrawler(self.policy)
        storage = self.storage

        pages_iter = crawler.crawled_pages()
        pre_fetch_pages = []
        pre_fetch_count = 0
        for page in pages_iter:
            pre_fetch_pages.append(page)

            pre_fetch_count += 1
            if pre_fetch_count >= MAXIMUM_PRE_FETCHES:
                break

        seeds = self._generate_seeds(pre_fetch_pages)
        parser_result = self.parser.probe(seeds)

        products_title = []
        for page in self._combine_iter(pre_fetch_pages, pages_iter):
            text_fields = parser_result.extract(page.url, page.content)

            if text_fields:
                info = self._extract(page, text_fields)
                title = info[TAG_TITLE]
                if title not in products_title:
                    products_title.append(title)
                    storage.add_or_update(storage.GROUPON,
                                          siteid = self.site,
                                          **info)
                else:
                    if TAG_CITY in info:
                        city = info[TAG_CITY]
                        groupon = storage.query(storage.GROUPON, title=title).get()

                        if not groupon.city:
                            groupon.city = city
                        elif city not in groupon.city:
                            groupon.city += u',' + city

                        groupon.put()

    def _init_cities(self):
        self.cities = {}
        soup = BeautifulSoup.BeautifulSoup(open(os.path.join(CURRENTDIR, CITIES_CONFIG), 'r'))

        for c in soup.findAll('city'):
            self.cities[c.text] = c['id']

    def _combine_iter(self, iter1, iter2):
        for i in iter1:
            yield i

        for i in iter2:
            yield i

    def _generate_seeds(self, pages):
        seeds = []
        cnt = len(pages)
        seed_num = min(20, cnt / 5)
        seed_list = []
        for i in range(0, seed_num):
            ind = random.randint(0, cnt - 1)
            while ind in seed_list:
                ind = random.randint(0, cnt - 1)

            seed_list.append(ind)
            seeds.append(pages[ind])

        return seeds

    def _extract(self, page, text_fields):
        info = {}
    
        # url
        info[TAG_URL] = page.url

        # city
        city = self._extract_city(page.linktext)
        if city:
            info[TAG_CITY] = city

        # title, image
        text_tags = [TAG_TITLE, TAG_IMAGE]
        for tag in text_tags:
            if tag in text_fields:
                info[tag] = self._extract_text(text_fields[tag])

        # original, saved, price_now, discount, items
        numeric_tags = [TAG_ORIGINAL, TAG_SAVED, TAG_PRICE, TAG_DISCOUNT, TAG_ITEMS]
        for tag in numeric_tags:
            if tag in text_fields:
                info[tag] = self._extract_number(text_fields[tag])

        return info

    def _extract_city(self, linktext):
        city = None

        if linktext != u'':
            long_link_text = False

            for t in linktext.split('/'):
                # city name should be longer than 2 chars
                if len(t) < 2:
                    continue

                if t in self.cities:
                    city = t
                    break

                if not long_link_text and len(t) >= 3:
                    long_link_text = True

            if not city and long_link_text:
                for c in self.cities:
                    if c in linktext:
                        city = c
                        break
            
        if city:
            return city
        else:
            print 'default city'
            print linktext
            return DEFAULT_CITY

    def _extract_text(self, text):
        return text

    def _extract_number(self, text):
        match = DIGITS_PATTERN.search(text)

        if match:
            return float(text[match.start():match.end()])
        else:
            return 0.0


