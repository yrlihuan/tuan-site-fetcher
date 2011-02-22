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

def validate_site_name(site):
    domain_surfix = '.appspot.com'

    if domain_surfix in site:
        return site

    if '.' not in site:
        return site + domain_surfix

class ManageRemoteData(webapp.RequestHandler):
    def get(self):
        self.response.out.write(ADMIN_PAGE)

class DisplayRemoteData(webapp.RequestHandler):
    def post(self):
        site = self.request.get('site')
        site = validate_site_name(site)
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

            entities = client.call_remote(site, DATASTORE, 'query', table, **params)
        except client.RPCException, ex:
            exception = ex

        out = self.response.out

        if exception:
            out.write(str(exception))
        else:
            out.write(datastore_query.get_html(entities))

class RemoveRemoteData(webapp.RequestHandler):
    def post(self):
        site = self.request.get('site')
        site = validate_site_name(site)
        table = self.request.get('table')

        try:
            client.call_remote(site, DATASTORE, 'remove', table)
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
