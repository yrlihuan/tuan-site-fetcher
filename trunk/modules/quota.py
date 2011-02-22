import wsgiref.handlers, urlparse, StringIO, logging, base64, zlib, re
import datetime
import cgi
import os
import os.path
import re
import sys
import urllib
import urllib2
import urlparse
import cookielib
import wsgiref.handlers
from datetime import date
from urllib import urlencode
from google.appengine.api import memcache
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.runtime import DeadlineExceededError
from google.appengine.ext.db import TransactionFailedError
from google.appengine.ext import webapp
from google.appengine.api import urlfetch
from google.appengine.api import urlfetch_errors
from google.appengine.api import urlfetch_stub
from google.appengine.api import apiproxy_stub_map
_DEBUG = True

CURRENTDIR = os.path.dirname(__file__)
ROOTDIR = os.path.join(CURRENTDIR, '..')
if ROOTDIR not in sys.path:
    sys.path.append(ROOTDIR)

from modules.BeautifulSoup import BeautifulSoup

CPU = 'cpu_usage'
OUT_BW = 'outgoing_bandwidth'
IN_BW = 'incomming_bandwidth'
STORE = 'datastore'
EMAIL = 'email'

CREDENTIAL_FILE = 'modules/credential'

def update():
    appid = os.environ['APPLICATION_ID']

    cf = open(CREDENTIAL_FILE, 'r')
    u_login = cf.readline()
    u_login.replace('\n', '')
    u_psw = cf.readline()
    u_psw.replace('\n', '')

    # based on http://stackoverflow.com/questions/101742/how-do-you-access-an-authenticated-google-app-engine-service-from-a-non-web-pyt
    serv_resp_body = ""
    #https://www.google.com/accounts/ServiceLogin?service=ah&continue=https://appengine.google.com/_ah/login%3Fcontinue%3Dhttps://appengine.google.com/dashboard%253Fapp_id%253Dwp-ge-admin&ltmpl=ae&sig=16b8025b156519ef5782af062efe55f8
    target_uri = 'https://appengine.google.com/dashboard?app_id=' + appid
    
    # we use a cookie to authenticate with Google App Engine
    #  by registering a cookie handler here, this will automatically store the 
    #  cookie returned when we use urllib2 to open http://currentcost.appspot.com/_ah/login
    cookiejar = cookielib.LWPCookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookiejar))
    urllib2.install_opener(opener)

    #
    # get an AuthToken from Google accounts
    #
    auth_uri = 'https://www.google.com/accounts/ClientLogin'
    authreq_data = urllib.urlencode({ "Email":   u_login,
                                      "Passwd":  u_psw,
                                      "service": "ah",
                                      "source":  appid,
                                      "accountType": "HOSTED_OR_GOOGLE" })
    auth_req = urllib2.Request(auth_uri, data=authreq_data)
    auth_resp = urllib2.urlopen(auth_req)
    auth_resp_body = auth_resp.read()
    # auth response includes several fields - we're interested in 
    #  the bit after Auth= 
    auth_resp_dict = dict(x.split("=")
                          for x in auth_resp_body.split("\n") if x)
    authtoken = auth_resp_dict["Auth"]
    #serv_resp_body += "AUTHCOOKIE:\n\n"+authtoken+"\n\n<hr>\n\n";

    serv_args = {}
    serv_args['continue'] = target_uri
    serv_args['pli']      = 1
    serv_args['auth']     = authtoken

    full_serv_uri = "https://appengine.google.com/_ah/login?%s" % (urllib.urlencode(serv_args))
    #serv_resp_body += "subrequest:\n\n"+full_serv_uri+"\n\n<hr>\n\n";
    
    serv_req = urllib2.Request(full_serv_uri)
    serv_resp = urllib2.urlopen(serv_req)
    serv_resp_body += serv_resp.read()

    # serv_resp_body should contain the contents of the 
    #  target_authenticated_google_app_engine_uri page - as we will have been 
    #  redirected to that page automatically 

    soup = BeautifulSoup(serv_resp_body)
    tags = [CPU, OUT_BW, IN_BW, STORE, EMAIL]
    result = {}
    pos = 0
    for node in soup.findAll(name='td', attrs={'class':'ae-quota-normal-text'}):
        value = float(node.text[0:-1])
        result[tags[pos]] = value
        pos += 1
    
    return result

