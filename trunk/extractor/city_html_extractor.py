import os.path
import sys
import logging
import re

CURRENTDIR = os.path.dirname(__file__)
ROOTDIR = os.path.join(CURRENTDIR, '..')
sys.path.append(CURRENTDIR)
sys.path.append(ROOTDIR)

from modules.BeautifulSoup import BeautifulSoup
from modules import urlfetch

sample_cities = ['beijing', 'shanghai', 'shenzhen', 'hangzhou']
CITYCONFIG = os.path.join(CURRENTDIR, 'cities.xml')
CITYPATTERN = re.compile('[a-zA-Z]+')

def process(data, siteid, cityurl, url, param, batchquery):
    """
    Extract city list from a html file
    Some web sites embed the city list in a html file (nuomi).
    Usually, the city names are listed in a single paragraph.
    This method generate neccessary urls based on the city list
    given in html file.
    """

    try:
        cityhtml = urlfetch.fetch(cityurl, retries=5, deadline=10)
    except:
        logging.exception('Error when retrieving city list html file')
        return None

    cities = get_cities(cityhtml)
    if not cities:
        return None

    urls = generate_groupon_urls(url, param, batchquery, cities)
    return urls

def get_cities(html):
    markup = BeautifulSoup(html)

    # search for text containing all the available cities
    search_exp = re.compile('shenzhen')
    citylisttext = None
    for node in markup.findAll(text=search_exp):
        nodetext = node
        count = 0
        for city in sample_cities:
            if city in nodetext:
                count += 1

        if count >= 3:
            citylisttext = nodetext
            break

    if not citylisttext:
        return None

    # the list containing all the cities
    fulllist = set()
    citycfg = BeautifulSoup(open(CITYCONFIG, 'r'))

    for n in citycfg.findAll('city'):
        fulllist.add(n['id'])

    # search for possible cities
    cities = []
    items = re.findall(CITYPATTERN, citylisttext)
    for item in items:
        if item in fulllist:
            cities.append(item)

    return cities

def generate_groupon_urls(base, param, batchquery, cities):
    urls = []

    cities_per_query = 10
    cities_this_query = 0
    batchquery = batchquery == '1'
    url = None
    for city in cities:
        if not url:
            url = base + '?'
        else:
            url += '&'

        url += param % city

        cities_this_query += 1
        if batchquery and cities_this_query <= cities_per_query:
            continue
        else:
            cities_this_query = 0
            urls.append(url)
            url = None

    if url:
        urls.append(url)

    return urls
    
