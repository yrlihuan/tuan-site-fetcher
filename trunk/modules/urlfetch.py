import logging

try:
    from google.appengine.api.urlfetch_errors import DownloadError
    from google.appengine.api import urlfetch
except:
    class DownloadError(Exception): pass
    urlfetch = None
    import urllib2

def fetch(url, data=None, deadline=None, retries=0):
    retry = 0

    # google api not available. use urllib2
    if not urlfetch:
        return urllib2.urlopen(url, data).read()

    method = data and urlfetch.POST or urlfetch.GET
    retry_cnt = 0
    
    while True:
        try:
            response = urlfetch.fetch(url, payload=data, method=method, deadline=deadline)
            return response.content
        except DownloadError, ex:
            logging.exception('urlfetch: error when accessing %s' % url)

            retry_cnt += 1
            if retry_cnt > retries:
                logging.error('urlfetch: exceeds maximum retry times. gives up')
                raise
            else:
                logging.error('urlfetch: retries: %d' % retry_cnt)
                continue
