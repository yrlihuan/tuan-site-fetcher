import os.path
import sys
import logging
import re
from modules.BeautifulSoup import BeautifulSoup

CURRENTDIR = os.path.dirname(__file__)
CITYCONFIG = os.path.join(CURRENTDIR, 'cities.xml')

NAMES_DICT = None
IDS_DICT = None

def city_names():
    if not NAMES_DICT:
        load_data()
    
    return NAMES_DICT

def city_ids():
    if not IDS_DICT:
        load_data()
    
    return IDS_DICT

def load_data():
    global NAMES_DICT
    global IDS_DICT

    NAMES_DICT = {}
    IDS_DICT = {}

    markup = BeautifulSoup(open(CITYCONFIG, 'r'))

    for node in markup.findAll('city'):
        city_id = node['id']
        city_name = node.text

        NAMES_DICT[city_name] = city_id
        IDS_DICT[city_id] = city_name

