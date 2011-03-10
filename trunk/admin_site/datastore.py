import sys
import os
import os.path
import cgi
import logging

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db

ADMIN_PAGE = open('html/datastore.html', 'r').read()

from rpc import client
from rpc.services import *
from html import datastore_query
import utils

class ManageRemoteData(webapp.RequestHandler):
    def get(self):
        self.response.out.write(ADMIN_PAGE)

class DisplayRemoteData(webapp.RequestHandler):
    def get(self):
        server = self.request.get('server')
        table = self.request.get('table')
        field = self.request.get('field')
        value = self.request.get('value')

        out = self.response.out

        try:
            entity = client.call_remote(server, DATASTORE, 'query', table, **{str(field):value})[0]
            for prop in vars(entity):
                out.write('<h1>%s:</h1><br/>%s<br/>' % (prop, unicode(getattr(entity, prop))))
        except Exception, ex:
            out.write(str(ex))
            return
        
        self.response.out.write(server)
        self.response.out.write(table)
        
    def post(self):
        server = self.request.get('server')
        server = utils.validate_site_name(server)
        table = self.request.get('table')
        param1_name = self.request.get('param1')
        param1_value = self.request.get('value1')
        param2_name = self.request.get('param2')
        param2_value = self.request.get('value2')

        try:
            exception = None
            params = {}

            # Why not using param1(2)_name directly? It seems Ver 2.5 only
            # supports str type as dict key, when using dict as func params
            if param1_name != '' and param1_value != '':
                params[str(param1_name)] = param1_value

            if param2_name != '' and param2_value != '':
                params[str(param2_name)] = param2_value

            entities = client.call_remote(server, DATASTORE, 'query', table, **params)
        except client.RPCException, ex:
            exception = ex

        out = self.response.out

        if exception:
            out.write(str(exception))
        else:
            out.write(datastore_query.get_html(entities, server, table))

class RemoveRemoteData(webapp.RequestHandler):
    def post(self):
        server = self.request.get('server')
        server = utils.validate_site_name(server)
        table = self.request.get('table')

        try:
            client.call_remote(server, DATASTORE, 'remove', table)
            self.response.out.write('Remove successfully')
        except exception, ex:
            self.response.out.write(str(ex))

application = webapp.WSGIApplication([('/datastore/admin', ManageRemoteData),
                                      ('/datastore/display', DisplayRemoteData),
                                      ('/datastore/remove', RemoveRemoteData)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
