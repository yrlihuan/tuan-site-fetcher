from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db

import os
import os.path
import logging
import sys
import traceback

CURRENTDIR = os.path.dirname(__file__)
sys.path.append(os.path.join(CURRENTDIR, '..'))

from rpc.messages import *

LOCAL_SERVER = os.environ['SERVER_NAME']

# the service:module mapping
SERVICES = {'datastore':'rpc.datastore_query_service'}

class RemoteCallHandler(webapp.RequestHandler):
    def authenticate(self):
        # TODO: add authentication code
        return True

    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write('For Test!')
        

    def post(self):
        if not self.authenticate():
            return

        self.response.headers['Content-Type'] = 'application/octet-stream'

        try:
            request = MessageBase.deserialize(self.request.body)
        except:
            logging.exception('RPC Handler: Exception when deserializing request!')

        caller = request._from
        service = request.service
        method = request.method
        params = request.params

        try:
            service_call = self.resolve_service_call(service, method)
            return_value = None
            exception = None
            callstack = None

            if service_call:
                return_value = service_call(**params)
            else:
                exception = Exception('Did not find corresponding method!')
        except Exception, ex:
            logging.exception('RPC Handler: Exception when executing RPC call!')
            exception = ex
            callstack = traceback.format_exc()

        response = Response(LOCAL_SERVER, caller, return_value, exception, callstack)
        response_data = MessageBase.serialize(response)

        self.response.out.write(response_data)

    def resolve_service_call(self, service, method):
        service_module = None
        method_func = None
        if service in SERVICES:
            module_name = SERVICES[service]
            if module_name not in sys.modules:
                service_module = __import__(module_name)
            else:
                service_module = sys.modules[module_name]

        if not service_module:
            logging.error('RPC Handler: Could not find module for service: %s' % service)
            return None

        if method in service_module.EXPORTS and hasattr(service_module, method):
            method_func = getattr(service_module, method)

        if not method_func:
            logging.error('RPC Handler: The method(%s) is not exposed by service' % method)

        return method_func

application = webapp.WSGIApplication(
                                     [('/rpc', RemoteCallHandler)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
