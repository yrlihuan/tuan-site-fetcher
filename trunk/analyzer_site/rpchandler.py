import logging

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db

from rpc.handler import RemoteCallHandler
from rpc.services import *

class RPCHandler(RemoteCallHandler):
    SERVICES = {DATASTORE:'datastore',
                SITEUPDATER:'analyzer.updatemanager'}

application = webapp.WSGIApplication(
                                     [('/rpc', RPCHandler)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()


