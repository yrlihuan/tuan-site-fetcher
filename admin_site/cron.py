import sys
import os
import os.path
import cgi
import urllib2
import logging

from google.appengine.api import taskqueue
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db

from modules import storage
from modules.BeautifulSoup import BeautifulSoup
from task_dispatcher import TaskDispatcher
from rpc.services import *
from rpc import client

class JobDispatcher(webapp.RequestHandler):
    def get(self):
        taskqueue.add(url='/cron/assign_jobs')

    def post(self):
        logging.info('task: assign_jobs started!')
        dispatcher = TaskDispatcher()
        dispatcher.balance_tasks()

class GrouponSync(webapp.RequestHandler):
    def get(self):
        for site in storage.query(storage.SITE):
            taskqueue.add(queue_name='grouponsync', \
                          url='/cron/sync_groupons', \
                          params={'siteid':site.siteid})

    def post(self):
        siteid = self.request.get('siteid')

        site = storage.query(storage.SITE, siteid=siteid).get()
        if not site or not site.updateserver:
            logging.error('GrouponSync: siteid or update server not valid')
            return

        try:
            entities = client.call_remote(site.updateserver, DATASTORE, 'query', storage.GROUPON, siteid=siteid)
            
            for server in storage.query(storage.SERVER, servertype='user'):
                logging.info('GrouponSync: Syncing data for site %s to server %s' % (siteid, server.address))
                client.call_remote(server.address, DBSYNC, 'sync', storage.GROUPON, entities, siteid=siteid)

        except client.RPCException, ex:
            logging.exception('GrouponSync: RPC exception when trying to sync site %s' % siteid)

application = webapp.WSGIApplication(
                                     [('/cron/assign_jobs', JobDispatcher),
                                      ('/cron/sync_groupons', GrouponSync)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()


