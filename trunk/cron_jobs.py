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

class UpdateSites(webapp.RequestHandler):
    def get(self):
        logging.info('Cron Job Triggered!')
        taskqueue.add(url='/cron/update_sites')

        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write('Cron Job - UpdateSites, Start Running!\n')

    def post(self):
        logging.info('task UpdateManager().run() started!')
        UpdateManager().run()

application = webapp.WSGIApplication(
                                     [('/cron/update_sites', UpdateSites)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

