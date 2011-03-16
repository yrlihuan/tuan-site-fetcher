import os
import sys
import os.path
import logging

import extractor
from extractor import GrouponInfo
from extractor.infotags import *
from modules.BeautifulSoup import BeautifulSoup
from modules import urlfetch

MAXIMUM_NEW_DATA = 50

def process(data, siteid, **params):
    """
    Extract extra fields from the web page for groupon products
    """
    if not isinstance(data, list) or \
       not isinstance(data[0], extractor.GrouponInfo):
        logging.error('HtmlExtractor: the input is not an array')
        return None

    props = {}
    for prop in params:
        value = params[prop]

        # the parameter could be path:xpath or attr:value
        if value.startswith('path:'):
            # if path for the node is provided, store the path
            # in the dictionary as a string
            props[prop] = value[5:]
        else:
            # if other property, store the attribute name and value
            # in the dictionary as a list
            props[prop] = value.split(':')

    failed_urls = []
    updated = []
    old = []

    cnt = 0
    for g in data:
        if not g.db_flag and cnt < MAXIMUM_NEW_DATA:
            updated.append(g)
            cnt += 1
        elif g.db_flag:
            old.append(g)

    for g in updated:
        try:
            page = urlfetch.fetch(g.url)
        except:
            logging.warning('HtmlExtractor: error accessing page %s' % g.url)
            failed_urls.append(g)
            continue

        try:
            markup = BeautifulSoup(page)
        except:
            logging.exception('HtmlExtractor: error when parsing html file!')
            continue

        for prop in props:
            value = props[prop]
            if isinstance(value, basestring):
                node = markup.get_node(value)
            else:
                attrs = {value[0]:value[1]}
                node = markup.find(attrs=attrs)

            if not node:
                logging.warning('HtmlExtractor: does not find node in page. Content length is %d, url %s' % (len(page), g.url))
                continue

            # convert the html content to unicode
            content = node.__str__(encoding=None)
            setattr(g, prop, content)

    # If detailed information can not be retrieved from web site page,
    # we remove the entry. The groupon info will be updated next time.
    data = []
    for g in updated:
        if g not in failed_urls:
            g.html_flag = True
            del g.db_flag
            data.append(g)    

    for g in old:
        g.html_flag = False
        del g.db_flag

    data.extend(old)
    return data

