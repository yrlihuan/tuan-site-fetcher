from storageimpl import StorageImpl
import sqlite3
import datetime
import os

SQLITEFILE = 'storage'

class Site(object):
    @classmethod
    def CreateTable(cls, conn):
        conn.execute("""
            create table site 
            (siteid text PRIMARY KEY)""")
        conn.commit()

class Page(object):
    @classmethod
    def CreateTable(cls, conn):
        conn.execute("""
            create table page 
            (url text PRIMARY KEY,
            siteid text,
            data text,
            updatedate timestamp,
            infopage boolean
            )""")
        conn.commit()

class SqliteStorage(StorageImpl):
    def __init__(self):

        sqlite3.register_adapter(bool, self.adapt_bool)
        sqlite3.register_converter('boolean', self.convert_bool)

        table_initialized = os.path.isfile(SQLITEFILE)
        self.conn = sqlite3.connect(SQLITEFILE, detect_types=sqlite3.PARSE_DECLTYPES)

        if not table_initialized:
            Site.CreateTable(self.conn)
            Page.CreateTable(self.conn)

    def query(self, table, **restrictions):
        script = ('SELECT * FROM %s ' % table) + self.generate_selection(**restrictions)
        cursor = self.conn.execute(script, restrictions)

        results = []
        result_type = self.get_type_for_table(table)
        for row in cursor:
            r = result_type()
            for ind, col in enumerate(cursor.description):
                setattr(r, col[0], row[ind])

            results.append(r)

        return results

    def create_or_update(self, table, primary_key, **properties):
        query = {primary_key:properties[primary_key]}
        rows = self.query(table, **query)

        is_update = len(rows) == 1
        
        if is_update:
            if len(properties) > 1: # update the record only if it has more than one properties
                script = self.generate_update(table, primary_key, **properties)
                self.conn.execute(script, properties)
                self.conn.commit()
        else:
            script = self.generate_insertion(table, **properties)
            self.conn.execute(script, properties)
            self.conn.commit()

    def delete(self, table, **restrictions):
        script = ('DELETE FROM %s' % table) + self.generate_selection(**restrictions)
        self.conn.execute(script, restrictions)

    def get_type_for_table(self, table):
        if table == 'site':
            return Site
        elif table == 'page':
            return Page
        else:
            raise TypeError('Can not determine appropriate type for table: %s' % table)

    def adapt_bool(self, b):
        return str(b)

    def convert_bool(self, s):
        return s == 'True'
