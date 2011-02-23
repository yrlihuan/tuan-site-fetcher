import sys
import os
import os.path
import cgi
import logging

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db

from rpc import client
from rpc.services import *
from modules import storage
from html import datastore_query

class ShowStatus(webapp.RequestHandler):
    def get(self):
        entities = self.get_db_entities(storage.SERVER)
        html_servers = datastore_query.get_html(entities)

        entities = self.get_db_entities(storage.SITE)
        html_sites = datastore_query.get_html(entities)

        html_status = open('html/status.html', 'r').read()

        self.response.out.write(html_status % (html_servers, html_sites))

    def get_db_entities(self, table):
        entities = []
        for entity in storage.query(table):
            obj = storage.EntityObject.clone_from_db_model(entity)
            entities.append(obj)

        return entities

class RestartUpdateTask(webapp.RequestHandler):
    def post(self):
        # to restart the whole process of analyzing, we should
        # 1. remove the datastore enties from update server
        # 2. remove the SITE entry from admin server
        # 3. wait for update server to trigger the whole update process
        site = self.request.get('site')
        out = self.response.out

        site_entity = storage.query(storage.SITE, siteid=site).get()
        if not site_entity:
            out.write('site id does not exist, or site has not been assigned to update server to run')
            return

        try:
            client.call_remote(site_entity.updateserver, DATASTORE, 'remove', '*', siteid=site)
            storage.delete(storage.SITE, siteid=site)
            out.write('Restart successfully')
        except exception, ex:
            out.write(str(ex))

application = webapp.WSGIApplication([('/update/status', ShowStatus),
                                      ('/update/restart', RestartUpdateTask)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()

