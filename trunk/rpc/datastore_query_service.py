import sys
import os
import os.path
import cgi

CURRENTDIR = os.path.dirname(__file__)
sys.path.append(os.path.join(CURRENTDIR, '..'))

from modules import storage

EXPORTS = ['query']

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

