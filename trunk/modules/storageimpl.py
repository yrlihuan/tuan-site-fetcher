"""
a simplified database interface.
the underlying database may either be sqlite or gae's datastorage.
"""

class StorageImpl(object):
    def __init__(self):
        pass
    
    def query(self, table, **restrictions):
        pass

    def create_or_update(self, table, primary_key, **properties):
        pass

    def delete(self, table, restrictions):
        pass

    def generate_selection(self, **restrictions):
        if restrictions == {}:
            return ''
        else:
            s = 'WHERE '
            for r in restrictions:
                s += '%s = :%s AND ' % (r, r)

            return s[:-5]

    def generate_insertion(self, table, **properties):
        collist = ''
        parametered_values = ''
        for p in properties:
            collist += '%s,' % p
            parametered_values += ':%s,' % p

        collist = collist[:-1]
        parametered_values = parametered_values[:-1]

        return 'INSERT INTO %s (%s) VALUES (%s)' % (table, collist, parametered_values)

    def generate_update(self, table, primary_key, **properties):
        primary_key_selection = {primary_key:properties.pop(primary_key)}
        selection = self.generate_selection(**primary_key_selection)

        update = ''
        for p in properties:
            update += '%s=:%s,' % (p, p)

        update = update[:-1]

        return ('UPDATE %s SET %s ' + selection) % (table, update)
