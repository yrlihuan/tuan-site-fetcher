import sys
import os
import os.path
import cgi

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db

from modules import storage

class MainPage(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write('Hello, webapp World!\n')

class TestOnly(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        helloworld = 'helloworld!'
        self.response.out.write(str(os.environ))


application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                     ('/testonly', TestOnly)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

