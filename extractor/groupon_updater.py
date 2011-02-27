import os
import sys
import os.path
import urllib2
import logging
from datetime import datetime
import time

from extractor import GrouponInfo
from extractor.infotags import *
from modules.storage import Groupon
from modules.storage import db
from modules import storage

def process(data, siteid):
    """
    This module stores the groupon data into datastore
    """
    data = convert_type(data)

    groupons = {}
    for g in storage.query(storage.GROUPON, siteid=siteid):
        groupons[g.url] = g

    for g in data:
        if g.url in groupons:
            db_entity = groupons[g.url]
            props = vars(g)
            for p in props:
                setattr(db_entity, p, props[p])
        else:
            db_entity = storage.Groupon(key_name=g.url, **vars(g))
            groupons[g.url] = db_entity

    db.put(groupons.values())

    return data

def convert_type(data):
    """
    This module converts data got from web site API to
    data types that is needed in our datastore
    """
    if not isinstance(data, list) or \
       not isinstance(data[0], GrouponInfo):
        logging.error('TypeConverter: the input is not an array')
        return None

    dbprops = Groupon._properties
    for grouponinfo in data:
        for prop in dbprops:
            if not hasattr(grouponinfo, prop):
                continue

            value = getattr(grouponinfo, prop)
            dbtype = dbprops[prop].data_type

            if isinstance(value, dbtype):
                continue

            if dbtype == datetime:
                dbvalue = time2datetime(value)
            else:
                dbvalue = dbtype(value)

            setattr(grouponinfo, prop, dbvalue)

    return data

def time2datetime(s):
    t = time.gmtime(float(s))
    return datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)
