import os
import sys
import os.path
import logging

import extractor
import urllib2
import xml.dom.minidom
from modules import geolib
from extractor import GrouponInfo
from extractor.infotags import *
from modules.BeautifulSoup import BeautifulSoup

MAXIMUM_NEW_DATA = 10

def process(data, siteid):
    """
    Extract geoinfo using google api
    """
    if not isinstance(data, list) or \
       not isinstance(data[0], extractor.GrouponInfo):
        logging.error('GoogleExtractor: the input is not an array')
        return None

    geofactory = geolib.GridFactory.get_factory()

    cnt = 0
    for g in data:
        if cnt >= MAXIMUM_NEW_DATA:
            break
            
        if (hasattr(g, 'geoinfo') and g.geoinfo) or \
           not (hasattr(g, 'address') and g.address ):
            continue

        cnt += 1
    
        try:
            addr = g.address.strip().replace(' ', '+')
            url = "http://maps.google.com/maps/api/geocode/xml?address=%s&sensor=false" % addr.encode('utf8')
            response = urllib2.urlopen(url)            
        except:
            logging.warning('GoogleExtractor: error accessing page %s' % url)
            continue

        try:
            markup = BeautifulSoup(response.read())            
        except:
            logging.exception('GoogleExtractor: XML error when parsing XML file!')
            continue

        if (markup.find('status').text == 'OK'):
            locationNode = markup.find('location')
            lat = locationNode.find('lat').text
            lng = locationNode.find('lng').text            
            setattr(g, 'geoinfo', '%s,%s' % (lat, lng))
            geopt = geolib.GeoPt(g.geoinfo)
            grid = geofactory.find_enclosure(geopt)
            g.geogrid = grid.get_id()
        elif (markup.find('status').text == 'ZERO_RESULTS'):
            setattr(g, 'geoinfo', u'90.0000000,0.0000000')            
        else:
            pass
    
    return data

