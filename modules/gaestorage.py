import datetime
from google.appengine.ext import db

from storageimpl import StorageImpl

class Site(db.Model):
    siteid = db.StringProperty(required=True)

class Page(db.Model):
    url = db.StringProperty(required=True)
    siteid = db.StringProperty(required=True)
    data = db.TextProperty()
    updatedate = db.DateTimeProperty()
    infopage = db.BooleanProperty()

class GaeStorage(StorageImpl):
    def __init__(self):
        pass
    
    def query(self, table, **restrictions):
        """
        query for entities in table
        return an iterable consisting of objects representing rows in database
        """
        t = self.get_type_for_table(table)

        if restrictions == {}:
            return t.all()
        else:
            query_str = self.generate_selection(**restrictions)
            return t.gql(query_str, **restrictions)

    def create_or_update(self, table, primary_key, **properties):
        """
        create an entity in table or update the old entity with new values
        """
        if primary_key not in properties:
            raise KeyError('missing key properties')

        datatype = self.get_type_for_table(table)
        key = properties[primary_key]

        entity = datatype.get_by_key_name(key)

        if not entity:
            entity = datatype(key_name=key, **properties)
        else:
            for prop in properties:
                setattr(entity, prop, properties[prop])
            
        entity.put()

    def delete(self, table, **restrictions):
        """
        remove table rows
        """
        for row in self.query(table, **restrictions):
            row.delete()

    def get_type_for_table(self, table):
        if table == 'site':
            return Site
        elif table == 'page':
            return Page
        else:
            raise TypeError('Can not determine appropriate type for table: %s' % table)

