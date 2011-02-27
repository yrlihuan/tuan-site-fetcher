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
import extractor

ADMIN_SERVER = 'tuanadminsite.appspot.com'

class Update(webapp.RequestHandler):
    def get(self):
        logging.info('Cron Job Triggered!')
        UpdateSites.enqueue_job()
        ReportStatus.enqueue_job()

        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write('Cron Job - UpdateSites, Start Running!\n')

class UpdateSites(webapp.RequestHandler):
    @classmethod
    def enqueue_job(cls):
        sites = []
        for site in storage.query(storage.SITE):
            siteid = site.siteid

            # If the enqueue time is later than last update, then it's very likely
            # that the work is still in queue. In this case, we don't put more tasks
            # into the queue.
            # One exception is, if last update time is 20 mins ago, we enqueue the task
            # anyway, in case that some unknown error happens and it failed to update
            # the lastupdate field in datastore.
            lastupdate = site.lastupdate
            enqueuetime = site.enqueuetime
            now = datetime.utcnow()
            if lastupdate and \
               enqueuetime and \
               enqueuetime > lastupdate and \
               now - lastupdate < timedelta(0, 1200, 0):
                logging.warning('Task_UpdateSites: Task is possibly in queue. Ignore it...')
                continue

            try:
                taskqueue.add(queue_name='grouponupdater', url='/cron/update_site', params={'siteid':siteid})
                site.enqueuetime = now
                sites.append(site)
            except:
                logging.exception('Task_UpdateSites: Failed to enqueue task %s!' % siteid)

        storage.db.put(sites)

    def post(self):
        siteid = self.request.get('siteid')
        site_entity = storage.query(storage.SITE, siteid=siteid).get()
        if not site_entity:
            logging.warning('Task_UpdateSites: site %s not found in datastore. Execution stops' % siteid)
            return

        try:
            extractor.update_site(siteid)
            site_entity.lastupdate = datetime.utcnow()
            site_entity.put()
        except:
            logging.exception('Task_UpdateSites: Error when execution!')
            return

class ReportStatus(webapp.RequestHandler):
    @classmethod
    def enqueue_job(cls):
        taskqueue.add(url='/cron/report_status')

    def post(self):
        logging.info('task ReportStatus started!')

        server = os.environ['SERVER_NAME']
        servertype = 'extractor'
        loads = quota.update()
        sites = []

        for site in storage.query(storage.SITE):
            entity_obj = storage.EntityObject.clone_from_db_model(site)
            sites.append(entity_obj)

        client.call_remote(ADMIN_SERVER, services.UPDATEADMIN, 'report', server, servertype, sites, loads)

application = webapp.WSGIApplication([('/cron/update', Update),
                                      ('/cron/update_site', UpdateSites),
                                      ('/cron/report_status', ReportStatus)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

