import sys
import os.path
import cgi

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db

from modules import storage
from modules import quota

class UpdateProgress(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write('Progresses for Sites!\n')

        out = self.response.out
        for site in storage.query(storage.SITE):
            out.write('-' * 20 + '\n')
            out.write(site.siteid + '\n')
            out.write(site.state + '\n')
            out.write(site.error + '\n')

        s = quota.update()
        out.write(str(s))
        
application = webapp.WSGIApplication(
                                     [('/update_progress', UpdateProgress)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

