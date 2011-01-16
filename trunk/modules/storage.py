"""
Provides a way to store data persistently. The real method for data
storage differs across platforms. On development machine, python's
standard module sqlite3 is used; while on google app engine, the data
storage api from GAE is used.

This module provides a unified way to access data storage submodule.
"""
import logging

storageimpl = None

try:
    from gaestorage import GaeStorage
    storageimpl = GaeStorage()
except Exception, ex:
    logging.info('test purpose only')
    logging.error(ex)

try:
    if not storageimpl:
        from sqlitestorage import SqliteStorage
        storageimpl = SqliteStorage()
except Exception, ex:
    logging.error(ex)

SITE = 'site'
PAGE = 'page'

def add_site(siteid):
    update_site(siteid)

def update_site(siteid, **properties):
    if 'siteid' not in properties:
        properties['siteid'] = siteid

    storageimpl.create_or_update(SITE, 'siteid', **properties)

def get_sites(**restrictions):
    return storageimpl.query(SITE, **restrictions)

def add_page(siteid, url, **properties):
    if 'siteid' not in properties:
        properties['siteid'] = siteid

    storageimpl.create_or_update(PAGE, 'url', **properties)

def update_page(url, **properties):
    if 'url' not in properties:
        properties['url'] = url

    storageimpl.create_or_update(PAGE, 'url', **properties)

def get_pages(**restrictions):
    return storageimpl.query(PAGE, **restrictions)

