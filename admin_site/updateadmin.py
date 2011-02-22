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
SITES_CFG = 'sites.xml'
RESERVED_LOAD = 25
SITES = None

def report(server, sites, loads):
    local_site_objs = []
    current_site = None
    for site in sites:
        local_obj = update_site_status(server, site)
        local_site_objs.append(local_obj)

        if Site.isrunning(site.state):
            if current_site:
                raise Exception('the report from update server shows it is running two analyzing job')
            current_site = site

    server_state = current_site and Server.STATE_RUNNING or Server.STATE_IDLE
    server_obj = update_server_entity(server, server_state, loads)

    if server_state == Server.STATE_IDLE:
        dispatch_update_work(server, loads)

def update_server_entity(server, state, loads):
    return storage.add_or_update(storage.SERVER, 'address', address=server, state=state, lastupdate=datetime.now(), **loads)

def update_site_status(server, entity_obj):
    entity = storage.query(storage.SITE, siteid=entity_obj.siteid).get()

    if entity and entity.updateserver != '' and entity.updateserver != server:
        raise Exception('one site is assigned to different update servers to analyze!')

    entity_obj.updateserver = server
    return storage.add_or_update(storage.SITE, 'siteid', **vars(entity_obj))

def dispatch_update_work(server, loads):

    # If the quota on the update server is lower than a certain level,
    # stop dispatching tasks to that server
    max_load = max(loads.values())
    if 100 - max_load < RESERVED_LOAD:
        return

    if not SITES:
        load_site_list()

    # Search for a site not dispatched to update server
    not_assigned_site = None
    for site in SITES:
        site_entity = storage.query(storage.SITE, siteid=site).get()
        if not site_entity:
            not_assigned_site = site
            break

    if not_assigned_site:
        storage.add_or_update(storage.SITE, 'siteid', siteid=site, updateserver=server)

        try:
            client.call_remote(server, SITEUPDATER, 'add_task', site)
        except:
            storage.delete(storage.SITE, siteid=site)   

def load_site_list():
    global SITES
    cfg = open(SITES_CFG, 'r')
    soup = BeautifulSoup(cfg)

    sites = []
    for node in soup.findAll('site'):
        sites.append(node.text)

    SITES = sites
    

