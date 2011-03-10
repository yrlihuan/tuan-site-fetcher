import logging
import math
from google.appengine.api import memcache
from google.appengine.ext import db
from modules import storage

ENTITIES_PER_BATCH = 20
ITERATION_BUF_SIZE = 20

def get_by_name(model_class, key_name):
    if isinstance(model_class, basestring):
        model_class = storage.get_type_for_table(model_class)

    if not model_class or not issubclass(model_class, db.Model):
        raise TypeError('CachedQuery: db.Model class or its class name expected! %s got!' % model_class)

    cached = memcache.get(key_name)
    if cached:
        return cached

    entity = model_class.get_by_key_name(key_name)
    if not entity:
        return None
    else:
        memcache.add(key_name, entity)
        return entity

class QueryStatus(object):
    def __init__(self):
        self.cached_results = []
        self.query_cursor = None
        self.query_finished = False

class CachedQuery(object):
    def __init__(self, model_class):
        if isinstance(model_class, basestring):
            model_class = storage.get_type_for_table(model_class)

        if not model_class or not issubclass(model_class, db.Model):
            raise TypeError('CachedQuery: db.Model class or its class name expected! %s got!' % model_class)

        self.query = None
        self.filters = {}
        self.orders = []
        self.finalized = False
        self.model_class = model_class
    
    def filter(self, property_op, value):
        if self.finalized:
            raise Exception('CachedQuery: can not change a finalized query')

        self.filters[property_op] = value

    def order(self, property):
        if self.finalized:
            raise Exception('CachedQuery: can not change a finalized query')

        self.orders.append(property)

    def get(self):
        ret = self.fetch(1)
        return len(ret) and ret[0] or None

    def fetch(self, limit, offset=0):
        if not self.finalized:
            self._finalize()

        end = offset + limit
        self._ensure(end)

        cached_results = self.status.cached_results

        cached_num = len(cached_results)
        if cached_num < end:
            end = cached_num
        
        key_names = cached_results[offset:end]
        if key_names:
            return self._get_entities_by_name(key_names)
        else:
            return []

    def __iter__(self):
        if not self.finalized:
            self._finalize()

        buf = None
        offset = 0
        while True:
            # if buf is nonempty, yield items in buf
            if buf:
                for entity in buf:
                    yield entity

                buf = None
                continue
        
            # if buf is empty, fill in with new items
            buf = self.fetch(ITERATION_BUF_SIZE, offset)
            if buf:
                offset += len(buf)
            else:
                # if there are no items, then the iteration ends
                return
            
    def _finalize(self):
        self.finalized = True
        self.sig = self._signature()

        status = memcache.get(self.sig)
        if not status:
            status = QueryStatus()
            added = memcache.add(self.sig, status)

            # update memcache entry
            if added:
                logging.info('CachedQuery: Cache added: %s' % self.sig)
            else:
                logging.warning('CachedQuery: Failed to add cache value: %s' % self.sig)
        else:
            logging.info('CachedQuery: Load query %s from cache!' % self.sig)

        self.status = status

    def _ensure(self, end):
        status = self.status
        cached = len(status.cached_results)
        if end <= cached or status.query_finished:
            return

        if not self.query:
            self._init_query()

        if status.query_cursor:
            self.query.with_cursor(status.query_cursor)
            fetch_num = self._entities_in_batch(end - cached)
            fetch_offset = 0
        else:
            fetch_num = self._entities_in_batch(end)
            fetch_offset = cached

        keys = self.query.fetch(limit=fetch_num, offset=fetch_offset)
        for key in keys:
            name = key.name()
            if name:
                status.cached_results.append(name)
            else:
                raise ValueError('CachedQuery: Can not get entity name!')

        status.query_finished = len(keys) < fetch_num

        try:
            status.query_cursor = self.query.cursor()
        except:
            # some queries don't support cursors
            status.query_cursor = None

        # update the memcache
        replaced = memcache.replace(self.sig, status)
        if replaced:
            logging.info('CachedQuery: Cache updated: %s' % self.sig)
        else:
            logigng.warning('CachedQuery: Failed to update cache value: %s' % self.sig)

    def _get_entities_by_name(self, names):
        # retrieve values from cache
        cached_values = memcache.get_multi(names)
        key_names = []
        for name in names:
            if name not in cached_values:
                key_names.append(name)

        # retrive values from datastore
        non_cached = {}
        entities = self.model_class.get_by_key_name(key_names)
        for ind in xrange(0, len(entities)):
            name = key_names[ind]
            entity = entities[ind]
            non_cached[name] = entity

        # update cache
        if non_cached:
            failed = memcache.add_multi(non_cached)
            if failed:
                for fail in failed:
                    logging.warning('CachedQuery: Failed to update cache value: %s' % fail)
            else:
                logging.info('CachedQuery: Cache batch update complete!')

        # build results
        ret = []
        for name in names:
            if name in cached_values:
                ret.append(cached_values[name])
            else:
                ret.append(non_cached[name])

        return ret

    def _init_query(self):
        query = db.Query(self.model_class, keys_only=True)

        for filter_op in self.filters:
            filter_value = self.filters[filter_op]
            query.filter(filter_op, filter_value)

        for order in self.orders:
            query.order(order)

        self.query = query

    def _signature(self):
        # The signature of the query is based on the query's filters and orders
        # Note that the uniqueness of the signature is guarenteed by the unique
        # string presentation of a dictionary. This is not a good solution but
        # probably the most straight forward one.
        return "CachedQuery%s%s" % (self.filters, self.orders)

    def _entities_in_batch(self, wanted):
        return (wanted / ENTITIES_PER_BATCH + 1) * ENTITIES_PER_BATCH

