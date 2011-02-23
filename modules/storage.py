"""
Provides a way to store data persistently. The real method for data
storage differs across platforms. On development machine, python's
standard module sqlite3 is used; while on google app engine, the data
storage api from GAE is used.

This module provides a unified way to access data storage submodule.
"""
import sys
import logging
import traceback

db = None
try:
    from google.appengine.ext import db
except Exception, ex:
    logging.error(ex)

if not db:
    import sqlitedb as db

MODULE = None

SITE = 'Site'
PAGE = 'Page'
PARSER = 'Parser'
GROUPON = 'Groupon'
SERVER = 'Server'

TABLES = [SITE, PAGE, PARSER, GROUPON, SERVER]

class Server(db.Model):
    # server states
    STATE_UNKNOWN = 'unknown'
    STATE_IDLE = 'idle'
    STATE_RUNNING = 'running'

    address = db.StringProperty(required=True)
    state = db.StringProperty(required=True)
    lastupdate = db.DateTimeProperty()
    cpu_usage = db.FloatProperty()
    outgoing_bandwidth = db.FloatProperty()
    incomming_bandwidth = db.FloatProperty()
    datastore = db.FloatProperty()
    email = db.FloatProperty()

class Site(db.Model):
    # site states
    STATE_INITIALIZING = 'initializing'
    STATE_PARSING = 'parsing'
    STATE_EXTRACTING = 'extracting'
    STATE_FINISHED = 'finished'
    STATE_ERROR = 'error'
    
    siteid = db.StringProperty(required=True)
    workerid = db.FloatProperty()
    state = db.StringProperty()
    updateserver = db.StringProperty()
    lastupdate = db.DateTimeProperty()
    error = db.TextProperty()
    data = db.TextProperty()
    groupon_count = db.IntegerProperty()

    @classmethod
    def isrunning(cls, state):
        return state == cls.STATE_INITIALIZING or state == cls.STATE_PARSING or state == cls.STATE_EXTRACTING

class Page(db.Model):
    url = db.StringProperty(required=True)
    siteid = db.StringProperty(required=True)
    data = db.TextProperty()
    updatedate = db.DateTimeProperty()
    infopage = db.BooleanProperty()
    parserid = db.IntegerProperty()
    linktext = db.StringProperty()

class Parser(db.Model):
    siteid = db.StringProperty(required=True)
    title = db.StringProperty()
    discount = db.StringProperty()
    original = db.StringProperty()
    saved = db.StringProperty()
    price_now = db.StringProperty()
    details = db.StringProperty()
    image = db.StringProperty()
    items = db.StringProperty()

class Groupon(db.Model):
    siteid = db.StringProperty(required=True)
    title = db.StringProperty(required=True)
    original = db.FloatProperty()
    discount = db.FloatProperty()
    saved = db.FloatProperty()
    items = db.FloatProperty()
    price_now = db.FloatProperty()
    image = db.StringProperty()
    url = db.StringProperty()
    city = db.TextProperty()

class EntityObject(object):
    model_properties_cache = {}

    @classmethod
    def get_properties(cls, db_model_cls):
        if db_model_cls in cls.model_properties_cache:
            props = cls.model_properties_cache[db_model_cls]
        else:
            props = []
            model_cls_props = vars(db_model_cls)
            for p in model_cls_props:
                if isinstance(model_cls_props[p], db.Property):
                    props.append(p)

            cls.model_properties_cache[db_model_cls] = props

        return props

    @classmethod
    def clone_from_db_model(cls, db_model):
        properties = cls.get_properties(db_model.__class__)
        entity_object = cls()

        for prop in properties:
            if hasattr(db_model, prop):
                value = getattr(db_model, prop)
                setattr(entity_object, prop, value)

        return entity_object

def text_type_converter(datatype, properties):
    for prop in properties:
        dbProperty = getattr(datatype, prop)
        if isinstance(dbProperty, db.TextProperty):
            properties[prop] = db.Text(properties[prop])

def linebreak_remover(datatype, properties):
    for prop in properties:
        dbProperty = getattr(datatype, prop)
        if isinstance(dbProperty, db.StringProperty) and '\n' in properties[prop]:
            properties[prop] = properties[prop].replace('\n', '')

def add_or_update(table, primarykey = None, **properties):
    datatype = get_type_for_table(table)
    text_type_converter(datatype, properties)
    linebreak_remover(datatype, properties)

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
    return entity

def query(table, **restrictions):
    t = get_type_for_table(table)
    text_type_converter(t, restrictions)
    linebreak_remover(t, restrictions)

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
    global MODULE
    if not MODULE:
        MODULE = sys.modules[__name__]

    if table in TABLES and hasattr(MODULE, table):
        return getattr(MODULE, table)
    else:
        raise TypeError('Can not determine appropriate type for table: %s' % table)


