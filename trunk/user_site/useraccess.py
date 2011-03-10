import sys
import os
import logging
import os.path
import cgi
import urllib2
from google.appengine.api import quota
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import memcache
from modules import storage
from modules import cachedquery
from modules.cachedquery import CachedQuery
from modules import storage

class ListGroupons(webapp.RequestHandler):
    """
    The handler for List action.
    params:
        city: city from city list
        orderby: [-bought, discount, current, -starttime]
        from, to: how many items
    """

    DEFAULT_FETCH_LEN = 20
    SUPPORTED_ORDERS = ['-bought', 'discount', 'current', '-starttime']

    def get(self):
        city = self.request.get('city')
        orderby = self.request.get('orderby')
        frmstr = self.request.get('from')
        tostr = self.request.get('to')

        if not city or not orderby:
            logging.error("ListGroupons: Query doesn't contain city or order")
            return

        if orderby not in ListGroupons.SUPPORTED_ORDERS:
            logging.error("ListGroupons: Query contains unsupported order %s" % orderby)
            return

        frm = 0
        if frmstr:
            try:
                frm = int(frmstr)
                if frm < 0:
                    frm = 0
            except ValueError:
                pass

        fetchlen = ListGroupons.DEFAULT_FETCH_LEN
        if tostr:
            try:
                to = int(tostr)
                if to > frm:
                    fetchlen = to - frm
            except ValueError:
                pass
        
        query = CachedQuery(storage.Groupon)
        query.filter('cityid =', city)
        query.order(orderby)

        self.response.headers['Content-Type'] = 'text/plain'        
        for entity in query.fetch(fetchlen, frm):
            self.response.out.write('url: %s\n' % entity.url)
            self.response.out.write('title: %s\n' % entity.title)
            self.response.out.write('started: %s\n' % entity.starttime)
            self.response.out.write('city: %s\n' % entity.city)
            self.response.out.write('bought: %s\n' % entity.bought)
            self.response.out.write('%s, %s, %s\n' % (entity.original, entity.discount, entity.current))

class RetrieveDetail(webapp.RequestHandler):
    def get(self):
        pass

application = webapp.WSGIApplication(
                                     [('/list', ListGroupons),
                                      ('/details', RetrieveDetail)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

