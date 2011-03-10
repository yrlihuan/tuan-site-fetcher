import sys
import os.path
import cgi
import logging
from datetime import datetime
from datetime import timedelta

from google.appengine.api import taskqueue
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from rpc import client
from rpc import services
from modules import quota
from modules import storage

ADMIN_SERVER = 'tuanadminsite.appspot.com'

class ReportStatus(webapp.RequestHandler):
    def get(self):
        taskqueue.add(queue_name='reportstatus', url='/cron/report_status')

    def post(self):
        logging.info('task ReportStatus started!')

        server = os.environ['SERVER_NAME']
        servertype = 'user'
        loads = quota.update()
        sites = []

        for site in storage.query(storage.SITE):
            entity_obj = storage.EntityObject.clone_from_db_model(site)
            sites.append(entity_obj)

        client.call_remote(ADMIN_SERVER, services.UPDATEADMIN, 'report', server, servertype, sites, loads)

application = webapp.WSGIApplication([('/cron/report_status', ReportStatus)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

