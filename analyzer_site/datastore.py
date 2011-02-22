import sys
import os
import os.path
import cgi

from modules import storage

EXPORTS = ['query', 'remove']

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

def remove(table):
    if table == '' or table == '*':
        storage.delete(storage.SITE)
        storage.delete(storage.GROUPON)
        storage.delete(storage.PARSER)
    else:
        storage.delete(table)

