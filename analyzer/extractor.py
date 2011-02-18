# coding=utf-8

import sys
import os.path
import random
import re

CURRENTDIR = os.path.dirname(__file__)
sys.path.append(os.path.join(CURRENTDIR, '..'))

from modules.BeautifulSoup import BeautifulSoup
from analyzer.pageparser import Parser
from crawler.simplecrawler import SimpleCrawler
from analyzer.tags import *

CITIES_CONFIG = 'cities.xml'
DIGITS_PATTERN = re.compile(u'\d+(\.\d+)?')
DEFAULT_CITY = u'北京'

class Extractor(object):
    def __init__(self):
        self._init_cities()
    
    def run(self, parser, page):
       text_fields = parser.extract(page.url, page.content)

       if text_fields:   
           return self._extract(page, text_fields)
       else:
           return None

    def _init_cities(self):
        self.cities = {}
        soup = BeautifulSoup(open(os.path.join(CURRENTDIR, CITIES_CONFIG), 'r'))

        for c in soup.findAll('city'):
            self.cities[c.text] = c['id']

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
            return DEFAULT_CITY

    def _extract_text(self, text):
        return text

    def _extract_number(self, text):
        match = DIGITS_PATTERN.search(text)

        if match:
            return float(text[match.start():match.end()])
        else:
            return 0.0


