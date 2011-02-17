"""
Provides a way to store data persistently. The real method for data
storage differs across platforms. On development machine, python's
standard module sqlite3 is used; while on google app engine, the data
storage api from GAE is used.

This module provides a unified way to access data storage submodule.
"""
import logging
import traceback

db = None
try:
    from google.appengine.ext import db
except Exception, ex:
    logging.error(ex)

if not db:
    import sqlitedb as db

class Site(db.Model):
    siteid = db.StringProperty(required=True)

class Page(db.Model):
    url = db.StringProperty(required=True)
    siteid = db.StringProperty(required=True)
    data = db.TextProperty()
    updatedate = db.DateTimeProperty()
    infopage = db.BooleanProperty()
    parserid = db.IntergerProperty()
    linktext = db.StringProperty()

class Parser(db.Model):
    parserid = db.IntergerProperty(required=True)
    siteid = db.StringProperty(required=True)
    title = db.StringProperty()
    discount = db.StringProperty()
    original = db.StringProperty()
    save = db.StringProperty()
    price_now = db.StringProperty()
    details = db.StringProperty()
    image = db.StringProperty()
    city = db.StringProperty()

class Groupon(db.Model):
    siteid = db.StringProperty(required=True)
    title = db.StringProperty(required=True)
    original = db.FloatProperty()
    discount = db.FloatProperty()
    saved = db.FloatProperty()
    items = db.FloatProperty()
    price_now = db.FloatProperty()
    image = db.StringProperty()
    city = db.StringProperty()
    url = db.StringProperty()

SITE = 'Site'
PAGE = 'Page'
PARSER = 'Parser'
GROUPON = 'Groupon'

def add_or_update(table, primarykey = None, **properties):
    datatype = get_type_for_table(table)

    if not primarykey or primarykey not in properties:
        key = None
        entity = None
    else:
        key = str(properties[primarykey])
        entity = datatype.get_by_key_name(key)

    if not entity:
        if key:
            entity = datatype(key_name=key, **properties)
        else:
            entity = datatype(**properties)
    else:
        for prop in properties:
            setattr(entity, prop, properties[prop])
        
    entity.put()

def query(table, **restrictions):
    t = get_type_for_table(table)

    if restrictions == {}:
        return t.all()
    else:
        query_str = generate_selection(**restrictions)
        return t.gql(query_str, **restrictions)

def delete(table, **restrictions):
    for entity in query(table, **restrictions):
        entity.delete()

def generate_selection(**restrictions):
    if restrictions == {}:
        return ''
    else:
        s = 'WHERE '
        for r in restrictions:
            s += '%s = :%s AND ' % (r, r)

        return s[:-5]

def get_type_for_table(table):
    if table == SITE:
        return Site
    elif table == PAGE:
        return Page
    elif table == PARSER:
        return Parser
    elif table == GROUPON:
        return Groupon
    else:
        raise TypeError('Can not determine appropriate type for table: %s' % table)