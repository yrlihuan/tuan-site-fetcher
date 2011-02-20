import sqlite3
import datetime
import random

class Text(unicode):
  def __new__(cls, arg=None, encoding=None):
    if arg is None:
      arg = u''
    if isinstance(arg, unicode):
      if encoding is not None:
        raise TypeError('Text() with a unicode argument '
                        'should not specify an encoding')
      return super(Text, cls).__new__(cls, arg)

    if isinstance(arg, str):
      if encoding is None:
        encoding = 'ascii'
      return super(Text, cls).__new__(cls, arg, encoding)

    raise TypeError('Text() argument should be str or unicode, not %s' %
                    type(arg).__name__)

def adapt_bool(b):
    return str(b)

def convert_bool(s):
    return s == 'True'

def adapt_ltext(text):
    return text

def convert_ltext(text):
    result = Text(text, 'utf8')
    return result

sqlite3.register_adapter(bool, adapt_bool)
sqlite3.register_converter('boolean', convert_bool)
sqlite3.register_adapter(Text, adapt_ltext)
sqlite3.register_converter('LTEXT', convert_ltext)

SQLITEFILE = 'storage'
CONN = sqlite3.connect(SQLITEFILE, detect_types=sqlite3.PARSE_DECLTYPES)
# CONN.text_factory = str

def create_sqlite_table(cls):
    try:
        table_name = cls.table
        init_list = ''

        for prop_name, prop_attr in cls._properties.items():
            init_list += ', %s %s' % (prop_name, prop_attr.SqlType)

        script = 'CREATE TABLE %s (key_name TEXT PRIMARY KEY%s)' % (table_name, init_list)
        CONN.execute(script)
        CONN.commit()
    except Exception, ex:
        # the table has already been created
        pass

def add_to_db(instance):
    properties = instance._get_db_properties()

    table = instance.table
    columns = ''
    parametered_values = ''
    for p in properties:
        columns += '%s,' % p
        parametered_values += ':%s,' % p

    columns = columns[:-1]
    parametered_values = parametered_values[:-1]
    
    script = 'INSERT INTO %s (%s) VALUES (%s)' % (table, columns, parametered_values)
    CONN.execute(script, properties)
    CONN.commit()
    
def save_to_db(instance):
    properties = instance._get_db_properties()

    table = instance.table
    assignments = ''
    for p in properties:
        if p != 'key_name':
            assignments += '%s=:%s,' % (p, p)

    assignments = assignments[:-1]

    script = 'UPDATE %s SET %s WHERE key_name=:key_name' % (table, assignments)
    CONN.execute(script, properties)
    CONN.commit()

def delete_from_db(instance):
    table = instance.table
    script = 'DELETE FROM %s WHERE key_name=:key_name' % table

    CONN.execute(script, {'key_name':instance.key_name})
    CONN.commit()

class DBProperty(object):
    def __init__(self, required=False):
        self.required = required

    def validate(self, value):
        return isinstance(value, self.Type)

Property=DBProperty

class IntegerProperty(DBProperty):
    Type = int
    SqlType = 'INTEGER'
    Default = 0

class DateTimeProperty(DBProperty):
    Type = datetime.datetime
    SqlType = 'TIMESTAMP'
    Default = datetime.datetime.now()

class BooleanProperty(DBProperty):
    Type = bool
    SqlType = 'BOOLEAN'
    Default = False

class StringProperty(DBProperty):
    Type = basestring
    SqlType = 'TEXT'
    Default = ''

class FloatProperty(DBProperty):
    Type = float
    SqlType = 'REAL'
    Default = 0.0

class TextProperty(DBProperty):
    Type = Text
    SqlType = 'LTEXT'
    Default = Text()

class Query(object):
    def __init__(self, entity_cls, query_str, **properties):
        self.entity_cls = entity_cls
        self.query_str = query_str
        self.properties = properties
        
    def __iter__(self):
        cursor = self._get_new_cursor()
        description = cursor.description
        for row in cursor:
            entity = self._convert_row(row, description)          
            yield entity

    def count(self, limit = 0):
        """ limit is ignored """
        cursor = self._get_new_cursor()
        return cursor.rowcount

    def get(self):
        cursor = self._get_new_cursor()
        description = cursor.description

        row = cursor.fetchone()
        entity = self._convert_row(row, description)
        return entity

    def fetch(self, limit, offset = 0):
        """ offset is ignored """
        cursor = self._get_new_cursor()
        description = cursor.description
        rows = cursor.fetchmany(limit)
        
        result = []
        for row in rows:
            entity = self._convert_row(row, description)
            result.append(entity)

        return result

    def _convert_row(self, row, description):
        if not row:
            return None

        properties = {}

        for ind, col in enumerate(description):
            col_name = col[0]
            properties[col_name] = row[ind]

        entity = self.entity_cls(**properties)
        entity.added = True

        return entity

    def _get_new_cursor(self):
        if self.query_str == '':
            return CONN.execute('SELECT * FROM %s' % self.entity_cls.table)
        else:
            return CONN.execute('SELECT * FROM %s %s' % (self.entity_cls.table, self.query_str), self.properties)

class PropertiedClass(type):
    def __init__(cls, name, bases, dct):
        if name == 'Model':
            return

        cls._properties = {}
        cls.table = name

        for varname in dct:
            if isinstance(dct[varname], DBProperty):
                cls._properties[varname] = dct[varname]

        create_sqlite_table(cls)

class Model(object):
    __metaclass__ = PropertiedClass

    def __init__(self, key_name = None, **properties):

        if not key_name:
            key_name = self._random_keyname()

        self.key_name = key_name

        for prop_name, prop_attr in self._properties.items():
            
            if prop_name in properties:
                prop_value = properties[prop_name]
                if not prop_attr.validate(prop_value):
                    raise TypeError('%s instead of %s is provided for property %s' \
                            % (str(type(prop_value)), str(prop_attr.Type), prop_name))
            elif not prop_attr.required:
                prop_value = prop_attr.Default
            else:
                raise Exception('%s is required!' % prop_name)

            setattr(self, prop_name, prop_value)

        self.added = False

    @classmethod
    def all(cls):
        return cls.gql('')

    @classmethod
    def gql(cls, query_str, **properties):
        return Query(cls, query_str, **properties)

    @classmethod
    def get_by_key_name(cls, key):
        try:
            return Query(cls, 'WHERE key_name = :key_name', key_name = key).__iter__().next()
        except:
            return None

    def put(self):
        if not self.added:
            try:
                add_to_db(self)
                self.added = True
                return
            except:
                # if exception is raised, we assume the record has already been added
                self.added = True

        save_to_db(self)

    def delete(self):
        if self.added:
            delete_from_db(self)

    def _get_db_properties(self):
        properties = {}

        properties['key_name'] = self.key_name

        for prop_name in self._properties:
            prop_value = getattr(self, prop_name)
            properties[prop_name] = prop_value

        return properties

    def _random_keyname(self):
        return str(random.randint(0, 1<<30))


