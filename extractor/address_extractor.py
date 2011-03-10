# coding=utf-8

import logging
import re
import cityutil
import urlparse
from modules.BeautifulSoup import BeautifulSoup
from modules.BeautifulSoup import NavigableString
from modules import geolib

ADDR_KEYWORDS = [u'市', u'区', \
                 u'街', u'路', u'里', u'弄', u'巷',\
                 u'大厦', u'号', u'层', u'楼', u'室', u'座']
KEYS_REQUIRED = 3
MARKUP_PATTERN = re.compile('<[^<>]*>')
GEOINFO_PATTERN = re.compile('\d+\.\d+,\d+\.\d+')
CITIES = cityutil.city_names()

CHINESE_COLON = u'：'

def process(data, siteid):
    """
    Functionality of this module:
    1. Remove html tags from shop field
    2. Get the address from detailed address info
    3. Get city id from city field
    """
    geofactory = geolib.GridFactory.get_factory()

    for g in data:
        mapdata = None
        if hasattr(g, 'shop'):
            shop_html = g.shop
            g.shop = re.sub(MARKUP_PATTERN, '', shop_html)

        if hasattr(g, 'city'):
            city = g.city
            if ',' in city:
                g.cityid = 'multi'
            elif city in CITIES:
                g.cityid = CITIES[city]

        if hasattr(g, 'addrdetails'):
            details = g.addrdetails
            del g.addrdetails

            markup = BeautifulSoup(details)
            address = get_addr_in_html(markup)
            if address:
                g.address = address

            geoinfo = get_geo_location_in_html(markup)
            if geoinfo:
                g.geoinfo = geoinfo

        if hasattr(g, 'mapimg'):
            mapimg = g.mapimg
            del g.mapimg

            if not hasattr(g, 'geoinfo'):
                markup = BeautifulSoup(mapimg)
                geoinfo = get_geo_location_in_html(markup)
                if geoinfo:
                    g.geoinfo = geoinfo

        if hasattr(g, 'geoinfo'):
            geoinfo = g.geoinfo.split(';')[0]
            geopt = geolib.GeoPt(geoinfo)
            grid = geofactory.find_enclosure(geopt)
            g.geogrid = grid.get_id()

    return data

def get_addr_in_html(markup):
    for tag in markup.recursiveChildGenerator():
        if not isinstance(tag, NavigableString):
            continue

        # address should be longer than 5 chars
        if len(tag) < 5:
            continue

        if CHINESE_COLON in tag:
            pos = tag.find(CHINESE_COLON)

            try:
                tag = tag[pos+1:]
            except:
                continue

        cnt = 0
        for key in ADDR_KEYWORDS:
            if key not in tag:
                continue
            
            cnt += 1
            if cnt >= KEYS_REQUIRED:
                return tag
                    
    return None

def get_geo_location_in_html(markup):
    for img in markup.findAll('img'):
        imgurl = None
        if img.has_key('src'):
            imgurl = img['src']
        elif img.has_key('lazysrc'):
            imgurl = img['lazysrc']

        if not imgurl:
            continue

        urlparts = urlparse.urlparse(imgurl)
        if 'google' not in urlparts.netloc:
            continue

        queries = urlparts.query.split('&')
        for q in queries:
            if not q.startswith('markers='):
                continue

            digit_pairs = re.findall(GEOINFO_PATTERN, q)
            if digit_pairs:
                return ';'.join(digit_pairs)


