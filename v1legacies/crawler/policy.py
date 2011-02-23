import os.path
import sys
import re

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from modules import BeautifulSoup

def read_config(config):
    buf = None
    if os.path.isfile(config):
        f = open(config, 'r')
        buf = f.read()
        f.close()
    elif hasattr(config, 'read'):
        buf = config.read()
        config.close()
    elif isinstance(config, basestring) and config[:5] == u'<?xml':
        buf = config
    else:
        raise TypeError('Can not import configuration from %s' % str(config))

    policy = CrawlerPolicy()
    soup = BeautifulSoup.BeautifulSoup(buf)

    site = soup.get_node('site')
    policy.site = site['id']

    starturls = soup.get_node('/site/starturls')
    for url in starturls('url'):
        policy.starturls.append(url.text)

    domains = soup.get_node('/site/domains')
    for s in domains('s'):
        policy.domains.append(s.text)
    for p in domains('p'):
        policy.domains.append(re.compile(p.text))

    patterns = soup.get_node('/site/patterns')
    for p in patterns('p'):
        policy.patterns.append(re.compile(p.text))

    maxdepth = soup.get_node('/site/maxdepth')
    policy.maximum_depth = int(maxdepth.text)

    maxpages = soup.get_node('/site/maxpages')
    policy.maximum_pages = int(maxpages.text)

    return policy

class CrawlerPolicy(object):
    def __init__(self):
        self.site = ''
        self.domains = []
        self.starturls = []
        self.patterns = []
        self.maximum_pages = 0
        self.maximum_depth = 0

