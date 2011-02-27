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

class JobDispatcher(webapp.RequestHandler):
    def get(self):
        taskqueue.add(url='/cron/assign_jobs')

    def post(self):
        logging.info('task: assign_jobs started!')
        dispatcher = TaskDispatcher()
        dispatcher.balance_tasks()

    def dispatch_update_work(self, server, loads):
    
        # If the quota on the update server is lower than a certain level,
        # stop dispatching tasks to that server
        max_load = max(loads.values())
        if 100 - max_load < RESERVED_LOAD:
            return
    
        # Search for a site not dispatched to update server
        not_assigned_site = None
        for site in SITES:
            site_entity = storage.query(storage.SITE, siteid=site).get()
            if not site_entity:
                not_assigned_site = site
                break
    
        if not_assigned_site:
            storage.add_or_update(storage.SITE, 'siteid', siteid=site, updateserver=server, lastupdate=datetime.utcnow())
    
            try:
                client.call_remote(server, SITEUPDATER, 'add_task', site)
            except:
                storage.delete(storage.SITE, siteid=site)   

application = webapp.WSGIApplication(
                                     [('/cron/assign_jobs', JobDispatcher)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()


