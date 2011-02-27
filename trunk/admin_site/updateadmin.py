import sys
import os
import os.path
import cgi
import logging
from datetime import datetime

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db

from rpc import client
from rpc.services import *
from modules import storage
from modules.storage import Server
from modules.storage import Site
from modules.BeautifulSoup import BeautifulSoup

EXPORTS = ['report']
RESERVED_LOAD = 25

def report(server, servertype, sites=[], loads=[]):
    site_prop = ''
    for site in sites:
        update_site_status(server, site)
        if site_prop == '':
            site_prop = site.siteid
        else:
            site_prop += ';' + site.siteid

    storage.add_or_update(storage.SERVER,
                          'address',
                          address=server,
                          sites=site_prop,
                          servertype=servertype,
                          lastupdate=datetime.utcnow(),
                          **loads)

def update_site_status(server, entity_obj):
    entity = storage.query(storage.SITE, siteid=entity_obj.siteid).get()
    entity_obj.updateserver = server
    return storage.add_or_update(storage.SITE, 'siteid', **vars(entity_obj))

