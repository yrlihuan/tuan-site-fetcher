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

HTTP_SCHEME = 'http'
RPC_HANDLER_ADDR = '/rpc'

if 'SERVER_NAME' in os.environ:
    LOCAL_SERVER = os.environ['SERVER_NAME']
else:
    LOCAL_SERVER = 'localhost'

class RPCExcpetion(Exception):
    pass

def call_remote(server, service, method, **params):

    try:
        remote_url = urlparse.urlunparse((HTTP_SCHEME, server, RPC_HANDLER_ADDR, '', '', ''))

        request_obj = Request(LOCAL_SERVER, server, service, method, **params)
        request_data = MessageBase.serialize(request_obj)

        response = urllib2.urlopen(remote_url, request_data)
        response_data = response.read()
        response_obj = MessageBase.deserialize(response_data)
    except Exception, ex:
        logging.exception('call_remote: error when executing RPC requests!')
        raise RPCExcpetion()

    if response_obj.exception:
        logging.error(response_obj.exception)
        logging.error(response_obj.callstack)
        raise RPCExcpetion()

    return response_obj.return_value
