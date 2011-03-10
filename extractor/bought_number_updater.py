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

MAXIMUM_NEW_DATA = 50
MINIMUM_CHANGE = 5

def process(data, siteid):
    """
    This module compares the data from web site api with the datastore data.
    If the groupon exists in datastore, it updates the sails number and remove
    it from the data colleciton, so it won't be processed by following modules.
    If the groupon is not in datastore, we keep leave it to module GrouponUpdater
    to save it.
    If some datastore groupons don't present in data set, it means the groupon is
    removed from the web site. Then remove it from the datastore
    """

    groupons = {}
    updated = []
    newdata = []
    for g in storage.query(storage.GROUPON, siteid=siteid):
        groupons[g.url] = g

    for g in data:
        if g.url in groupons:
            db_entity = groupons.pop(g.url)
            newvalue = int(g.bought)
            oldvalue = db_entity.bought

            # in order to reduce datastore API calls, only update the
            # bought number when the change is significant enough
            if newvalue - oldvalue > MINIMUM_CHANGE:
                db_entity.bought = int(g.bought)
                updated.append(db_entity)
        else:
            newdata.append(g)

    # save the bought numbers to datastore
    if len(updated):
        db.put(updated)

    # if there are old entities not availble any longer, remove them
    if len(groupons):
        db.delete(groupons.values())

    # pass new data to further processing
    if len(newdata) > MAXIMUM_NEW_DATA:
        return newdata[0:MAXIMUM_NEW_DATA]
    else:
        return newdata
