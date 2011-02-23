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
_DEBUG = True

CURRENTDIR = os.path.dirname(__file__)
ROOTDIR = os.path.join(CURRENTDIR, '..')
if ROOTDIR not in sys.path:
    sys.path.append(ROOTDIR)

from modules.BeautifulSoup import BeautifulSoup
from modules.BeautifulSoup import NavigableString

CPU = 'cpu_usage'
OUT_BW = 'outgoing_bandwidth'
IN_BW = 'incomming_bandwidth'
STORE = 'datastore'
EMAIL = 'email'

KEYWORDS = {re.compile('\s*CPU Time'):CPU,
            re.compile('\s*Outgoing Bandwidth'):OUT_BW,
            re.compile('\s*Incoming Bandwidth'):IN_BW,
            re.compile('\s*Total Stored Data'):STORE,
            re.compile('\s*Recipients Emailed'):EMAIL}

CREDENTIAL_FILE = 'modules/credential'

EMPTY_PATTERN = re.compile(u'\A\s*\Z')

def get_data_for_node(node):
    value = float(node.text[0:-1])

    desc_text = None
    for n in node.previousGenerator():
        if not isinstance(n, NavigableString) or EMPTY_PATTERN.match(n):
            continue

        desc_text = n
        break

    if not desc_text:
        return None, None

    key = None
    for keyword in KEYWORDS:
        if keyword.match(desc_text):
            key = KEYWORDS[keyword]
            break

    if not key:
        return None, None
    else:
        return key, value

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
    result = {}
    node_alert = soup.findAll(name='td', attrs={'class':'ae-quota-alert-text'})
    node_normal = soup.findAll(name='td', attrs={'class':'ae-quota-normal-text'})

    for node in node_alert:
        key, value = get_data_for_node(node)
        if key:
            result[key] = value

    for node in node_normal:
        key, value = get_data_for_node(node)
        if key:
            result[key] = value
    
    return result

