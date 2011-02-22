import sys
import os.path
import cgi
import logging

from google.appengine.api import taskqueue
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from analyzer.updatemanager import UpdateManager
from rpc import client
from rpc import services
from modules import quota
from modules import storage

ADMIN_SERVER = 'tuanadminsite.appspot.com'

class Update(webapp.RequestHandler):
    def get(self):
        logging.info('Cron Job Triggered!')
        taskqueue.add(url='/cron/report_status')
        taskqueue.add(url='/cron/update_sites')

        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write('Cron Job - UpdateSites, Start Running!\n')

class UpdateSites(webapp.RequestHandler):
    def post(self):
        logging.info('task UpdateManager().run() started!')
        UpdateManager().run()

class ReportStatus(webapp.RequestHandler):
    def post(self):
        logging.info('task ReportStatus started!')

        server = os.environ['SERVER_NAME']
        loads = quota.update()
        sites = []

        for site in storage.query(storage.SITE):
            entity_obj = storage.EntityObject.clone_from_db_model(site)
            entity_obj.data = db.Text(u'')
            sites.append(entity_obj)

        client.call_remote(ADMIN_SERVER, services.UPDATEADMIN, 'report', server, sites, loads)

application = webapp.WSGIApplication([('/cron/update', Update),
                                      ('/cron/update_sites', UpdateSites),
                                      ('/cron/report_status', ReportStatus)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

