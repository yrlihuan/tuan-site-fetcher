import sys
import os
import os.path
import cgi
import logging

from modules import storage

EXPORTS = ['sync']

def sync(table, data, **restrictions):
    """
    Remote server calls this to make the user site sync datastore
    entities based on data from remote.
        table: db model type
        data: collection consisted of updated entities
        restrictions: detailed rules to select data
    """
    
    model_cls = storage.get_type_for_table(table)
    keyprop = model_cls.keyprop
    updated = 0
    created = 0
    deleted = 0
    
    db_entities = {}
    for entity in storage.query(table, **restrictions):
        keyvalue = getattr(entity, keyprop)
        db_entities[keyvalue] = entity

    updatedlist = []
    for entity_obj in data:
        keyvalue = getattr(entity_obj, keyprop)

        if keyvalue in db_entities:
            entity = db_entities.pop(keyvalue)

            if storage.EntityObject.populate_db_model(entity_obj, entity):
                updatedlist.append(entity)
                updated += 1
        else:
            entity = model_cls(key_name=keyvalue, **vars(entity_obj))
            updatedlist.append(entity)
            created += 1

    storage.db.put(updatedlist)
    storage.db.delete(db_entities.values())

    logging.info('DBSync: Sync for entities with restrictions %s' % restrictions)
    logging.info('DBSync: Created %d' % created)
    logging.info('DBSync: Updated %d' % updated)
    logging.info('DBSync: Deleted %d' % deleted)

