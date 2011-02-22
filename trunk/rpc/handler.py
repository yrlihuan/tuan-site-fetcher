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

# these ip addresses belong to google
class RemoteCallHandler(webapp.RequestHandler):
    # the service:module mapping
    # derived class (usually on different server) should override
    # this default mapping to use server specific values
    SERVICES = {}

    def authenticate(self):
        return True

    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write('For Test!')
        

    def post(self):
        # TODO: uncomment the code to be more secure
        # if not self.authenticate():
        #     return

        self.response.headers['Content-Type'] = 'application/octet-stream'

        try:
            request = MessageBase.deserialize(self.request.body)
        except:
            logging.exception('RPC Handler: Exception when deserializing request!')

        caller = request._from
        service = request.service
        method = request.method
        args = request.args
        params = request.params

        try:
            return_value = None
            exception = None
            callstack = None

            service_call = self.resolve_service_call(service, method)
            if service_call:
                return_value = service_call(*args, **params)
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
        if service in self.SERVICES:
            module_name = self.SERVICES[service]
            if module_name not in sys.modules:
                service_module = __import__(module_name)

            service_module = sys.modules[module_name]

        if not service_module:
            logging.error('RPC Handler: Could not find module for service: %s' % service)
            return None

        if method in service_module.EXPORTS and hasattr(service_module, method):
            method_func = getattr(service_module, method)

        if not method_func:
            logging.error('RPC Handler: The method(%s) is not exposed by service' % method)

        return method_func

