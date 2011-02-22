import sys
import os
import os.path
import cgi
import urllib2

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db

from modules import storage

class MainPage(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write('Hello, webapp World!?\n')

        request = urllib2.Request('http://groupon2334.appspot.com/testonly',
                                  None, # data
                                  {'USER_AGENT':'DUMMY AGENT'}) # headers
        response = urllib2.urlopen(request)

        self.response.out.write('remote info:\n')
        self.response.out.write(response.read())

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

