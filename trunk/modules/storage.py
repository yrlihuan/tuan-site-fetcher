"""
Provides a way to store data persistently. The real method for data
storage differs across platforms. On development machine, python's
standard module sqlite3 is used; while on google app engine, the data
storage api from GAE is used.

This module provides a unified way to access data storage submodule.
"""
import sys
import os.path
import logging
import traceback
import time

db = None
try:
    from google.appengine.ext import db
except Exception, ex:
    logging.error(ex)

if not db:
    import sqlitedb as db

MODULE = None

SITE = 'Site'
GROUPON = 'Groupon'
SERVER = 'Server'

TABLES = [SITE, GROUPON, SERVER]

class Server(db.Model):
    keyprop = 'address'
    address = db.StringProperty(required=True)
    servertype = db.StringProperty()
    sites = db.StringProperty()
    lastupdate = db.DateTimeProperty()
    cpu_usage = db.FloatProperty()
    outgoing_bandwidth = db.FloatProperty()
    incomming_bandwidth = db.FloatProperty()
    datastore = db.FloatProperty()
    email = db.FloatProperty()

class Site(db.Model):
    keyprop = 'siteid'
    siteid = db.StringProperty(required=True)
    updateserver = db.StringProperty()
    enqueuetime = db.DateTimeProperty()
    lastupdate = db.DateTimeProperty()
    error = db.TextProperty()
    data = db.BlobProperty()

class Groupon(db.Model):
    keyprop = 'url'
    url = db.StringProperty(required=True)
    siteid = db.StringProperty()
    sitename = db.StringProperty()
    title = db.StringProperty()
    shop = db.TextProperty()
    image = db.StringProperty()
    address = db.TextProperty()
    city = db.TextProperty()
    cityid = db.StringProperty()
    geoinfo = db.StringProperty()
    details = db.TextProperty()
    detailsimg = db.TextProperty()
    category = db.StringProperty()
    bought = db.IntegerProperty()
    original = db.FloatProperty()
    discount = db.FloatProperty()
    saved = db.FloatProperty()
    current = db.FloatProperty()
    geogrid = db.IntegerProperty()
    starttime = db.DateTimeProperty()
    duetime = db.DateTimeProperty()

class EntityObject(object):
    @classmethod
    def get_properties(cls, db_model_cls):
        return db_model_cls._properties

    @classmethod
    def clone_from_db_model(cls, db_model):
        properties = cls.get_properties(db_model.__class__)
        entity_object = cls()

        for prop in properties:
            if hasattr(db_model, prop):
                value = getattr(db_model, prop)
                setattr(entity_object, prop, value)

        return entity_object

    @classmethod
    def populate_db_model(cls, entity_obj, db_model):
        properties = cls.get_properties(db_model.__class__)

        updated = False
        for prop in properties:
            if hasattr(entity_obj, prop):
                value = getattr(entity_obj, prop)
            else:
                value = properties[prop].default_value()

            oldvalue = getattr(db_model, prop)
            if value != oldvalue:
                setattr(db_model, prop, value)
                updated = True

        return updated

    @classmethod
    def update_db_model(cls, entity_obj, db_model):
        properties = vars(entity_obj)

        for prop in properties:
            setattr(db_model, prop, properties[prop])

class GrouponPatch(object):
    def __init__(self, site, version, db_models):
        self.dbtype = Groupon
        self.keyprop = self.dbtype.keyprop
        self.site = site
        self.updated = {}
        self.deleted = set()
        self.created = {}
        self.basevalues = set()
        self.version = version
        
        for entity in db_models:
            keyvalue = self._get_key(entity)
            self.basevalues.add(keyvalue)

    def update(self, db_model, prop, value):
        if getattr(db_model, prop) == value:
            return
        else:
            keyvalue = self._get_key(db_model)
            entity_obj = self._get_entity_to_update()
            setattr(entity_obj, prop, value)

    def create(self, **props):
        keyvalue = props[self.keyprop]
        entity_obj = self._get_entity_to_add(keyvalue)
        for prop in props:
            setattr(entity_obj, prop, props[prop])

    def delete(self, db_model):
        keyvalue = self._get_key(db_model)
        if keyvalue not in self.basevalues:
            raise Exception('GrouponPatch: Trying to delete a nonexist entity!')

        self.deleted.add(keyvalue)

    def apply_patch(self, db_models):
        if isinstance(db_models, dict):
            old_entities = db_models
        else:
            old_entities = {}
            for db_model in db_models:
                keyvalue = self._get_key(db_model)
                old_entities[keyvalue] = db_model

        updated = []
        for key in self.updated:
            if key in old_entities:
                entity_obj = self.updated[key]
                db_model = old_entities[key]
                EntityObject.update_db_model(entity_obj, db_model)
                updated.append(db_model)
            else:
                raise Exception('GrouponPatch: Trying to patch updated items. But db entity not found!')

        for key in self.created:
            if key in old_entities:
                raise Exception('GrouponPatch: Trying to patch created items. But db entity already exists!')
            else:
                entity_obj = self.created[key]
                db_model = self.dbtype(key_name=key, **vars(entity_obj))
                updated.append(db_model)

        deleted = []
        for key in self.deleted:
            if key in old_entities:
                deleted.append(old_entities[key])
            else:
                raise Exception('GrouponPatch: Trying to patch deleted items. But db entity not found!')

        db.put(updated)
        db.delete(deleted)

    def _get_key(self, db_model):
        return getattr(db_model, self.keyprop)

    def _get_entity_to_update(self, keyvalue):
        if keyvalue in self.updated:
            return self.updated[keyvalue]
        elif keyvalue in self.created:
            return self.created[keyvalue]
        elif keyvalue in self.deleted:
            raise Exception('GrouponPatch: Trying to update a deleted entity!')
        elif keyvalue in self.basevalues:
            entity_obj = EntityObject()
            self.updated[keyvalue] = entity_obj
            return entity_obj
        else:
            raise Exception('GrouponPatch: Trying to update a nonexist entity!')

    def _get_entity_to_add(self, keyvalue):
        if keyvalue in self.basevalues:
            raise Exception('GrouponPatch: Trying to create an exist entity!')
        else:
            entity_obj = EntityObject()
            self.created[keyvalue] = entity_obj
            return entity_obj
    
    @classmethod
    def serialize(cls, patch):
        return pickle.dumps(patch)

    @classmethod
    def deserialize(cls, s):
        return pickle.loads(s)

def text_type_converter(datatype, properties):
    for prop in properties:
        dbProperty = getattr(datatype, prop)
        if isinstance(dbProperty, db.TextProperty):
            properties[prop] = db.Text(properties[prop])
        elif isinstance(dbProperty, db.BlobProperty):
            properties[prop] = db.Blob(properties[prop])

def linebreak_remover(datatype, properties):
    for prop in properties:
        dbProperty = getattr(datatype, prop)
        if isinstance(dbProperty, db.StringProperty) and '\n' in properties[prop]:
            properties[prop] = properties[prop].replace('\n', '')

def add_or_update(table, **properties):
    datatype = get_type_for_table(table)
    text_type_converter(datatype, properties)
    linebreak_remover(datatype, properties)

    primarykey = datatype.keyprop
    key = properties[primarykey]
    entity = datatype.get_by_key_name(key)

    if not entity:
        updated = True
        entity = datatype(key_name=key, **properties)
    else:
        updated = False
        for prop in properties:
            oldvalue = getattr(entity, prop)
            newvalue = properties[prop]
            if oldvalue != newvalue:
                updated = True
                setattr(entity, prop, newvalue)

    if updated:
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


