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

def report(server, servertype, sites=None, loads=None):
    if sites is None:
        sites = []

    if loads is None:
        loads = {}

    site_prop = ''

    # Get all sites that assigned to this server
    obsolete_sites = {}
    for site in storage.query(storage.SITE, updateserver=server):
        obsolete_sites[site.siteid] = site
    
    # Update sites in report
    for site in sites:
        if site.siteid in obsolete_sites:
            obsolete_sites.pop(site.siteid)
            update_site_entity = True
        else:
            old_entity = storage.query(storage.SITE, siteid=site.siteid).get()
            if old_entity and old_entity.updateserver and old_entity.updateserver != server:
                update_site_entity = False
            else:
                update_site_entity = True
        
        # update the site entity
        if update_site_entity:
            site.updateserver = server
            storage.add_or_update(storage.SITE, **vars(site))

        # build sites list to save in server entity
        if site_prop == '':
            site_prop = site.siteid
        else:
            site_prop += ';' + site.siteid

    # Remove obsolete sites
    if len(obsolete_sites) > 0:
        storage.db.delete(obsolete_sites.values())

    # Save server entity
    storage.add_or_update(storage.SERVER,
                          address=server,
                          sites=site_prop,
                          servertype=servertype,
                          lastupdate=datetime.utcnow(),
                          **loads)

