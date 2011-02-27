import os
import sys
import os.path
import logging

import extractor
from extractor.infotags import *
from modules.BeautifulSoup import BeautifulSoup
from modules import urlfetch

PROPERTY_MAPPING = {'loc':GROUPON_URL,
                    'website':GROUPON_SITENAME,
                    'city':GROUPON_CITY,
                    'category':GROUPON_CATEGORY,
                    'address':GROUPON_ADDRESS,
                    'title':GROUPON_TITLE,
                    'image':GROUPON_IMAGE,
                    'starttime':GROUPON_STARTTIME,
                    'endtime':GROUPON_ENDTIME,
                    'value':GROUPON_ORIGINAL,
                    'price':GROUPON_CURRENT,
                    'rebate':GROUPON_DISCOUNT,
                    'bought':GROUPON_BOUGHT}

def process(data, siteid, url=None):
    """
    Get the groupon info list from a list of urls
    The info is stored following hao123's API standard
    """
    if data:
        urls = data
    elif url:
        urls = [url]
    else:
        return None

    result = []
    for url in urls:
        try:
            content = urlfetch.fetch(url, retries=5, deadline=10)
        except:
            logging.exception('Error when accessing page: %s' % url)
            continue

        markup = BeautifulSoup(content)
        for item in markup.findAll('url'):
            properties = {}
            for n in item.recursiveChildGenerator():
                if hasattr(n, 'name') and n.name in PROPERTY_MAPPING:
                    pname = PROPERTY_MAPPING[n.name]
                    properties[pname] = n.text

            grouponinfo = extractor.GrouponInfo(siteid)
            grouponinfo.set_props(properties)
            result.append(grouponinfo)

    return result
