import sys
import os
import os.path
import logging
import urllib2
import urlparse

CURRENTDIR = os.path.dirname(__file__)
ROOTDIR = os.path.join(CURRENTDIR, '..')
if ROOTDIR not in sys.path:
    sys.path.append(ROOTDIR)

from rpc.messages import *
from google.appengine.api import urlfetch

HTTP_SCHEME = 'http'
RPC_HANDLER_ADDR = '/rpc'

if 'SERVER_NAME' in os.environ:
    LOCAL_SERVER = os.environ['SERVER_NAME']
else:
    LOCAL_SERVER = 'localhost'

class RPCException(Exception):
    pass

def call_remote(server, service, method, *args, **params):

    try:
        remote_url = urlparse.urlunparse((HTTP_SCHEME, server, RPC_HANDLER_ADDR, '', '', ''))

        request_obj = Request(LOCAL_SERVER, server, service, method, *args, **params)
        request_data = MessageBase.serialize(request_obj)

        response = urlfetch.fetch(remote_url, method=urlfetch.POST, payload=request_data, deadline=15)
        response_data = response.content
        response_obj = MessageBase.deserialize(response_data)
    except Exception, ex:
        logging.exception('call_remote: error when executing RPC requests!')
        raise RPCException('RPC.Client: Error when executing RPC requests')

    if response_obj.exception:
        logging.error(response_obj.exception)
        logging.error(response_obj.callstack)
        raise RPCException('RPC.Client: Error when executing RPC requests')

    return response_obj.return_value
