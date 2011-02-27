import sys
import os
import os.path
import cgi

from modules import storage

EXPORTS = ['query', 'remove', 'add_task']

def query(table, limit=0, **restrictions):
    query_result = storage.query(table, **restrictions)

    if query_result == None:
        return None

    count = 0

    result = []
    for entity in query_result:
        entity_obj = storage.EntityObject.clone_from_db_model(entity)
        result.append(entity_obj)

        count += 1
        if limit > 0 and count >= limit:
            break

    return result

def remove(table, **restrictions):
    tables = []
    if not table or table == '' or table == '*':
        tables.append(storage.SITE)
        tables.append(storage.GROUPON)
        tables.append(storage.PARSER)
    else:
        tables.append(table)
    
    for t in tables:
        storage.delete(t, **restrictions)

def add_task(siteid):
    if storage.query(storage.SITE, siteid=siteid).get():
        return

    storage.add_or_update(storage.SITE, siteid=siteid)
