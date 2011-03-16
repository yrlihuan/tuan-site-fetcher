import urllib2
import os.path
import sys
import logging
import xml.dom.minidom
from datetime import datetime

CURRENTDIR = os.path.dirname(__file__)
ROOTDIR = os.path.join(CURRENTDIR, '..')
sys.path.append(CURRENTDIR)
sys.path.append(ROOTDIR)

from modules import storage

CONFIG_FILE = os.path.join(CURRENTDIR, 'configs.xml')
CONFIGS = None

class SiteConfig():
    def __init__(self, sitenode):
        self.siteid = sitenode.attributes['id'].value
        self.sitenode = sitenode

    def get_processors(self):
        processors = self.sitenode.getElementsByTagName('processor')
        for processor in processors:
            module = processor.attributes['module'].value
            params = {}
            for n in processor.childNodes:
                if n.nodeType in (n.TEXT_NODE, n.CDATA_SECTION_NODE):
                    continue
                params[str(n.nodeName)] = n.childNodes[0].data

            yield module, params

class GrouponInfo():
    def __init__(self, siteid):
        self.siteid = siteid

    def set_props(self, props):
        for prop in props:
            setattr(self, prop, props[prop])

    def __str__(self):
        s = ''
        for p in vars(self):
            s += p + '\t'

        return s

def get_config(siteid):
    load_configs()
    return CONFIGS.get(siteid)

def load_configs():
    global CONFIGS
    if CONFIGS:
        return

    configs = {}
    try:
        config_dom = xml.dom.minidom.parse(CONFIG_FILE)
    except Exception, e:
        print "xml error!"
    sitelist = config_dom.getElementsByTagName('site')
    for sitenode in sitelist:
        siteid = sitenode.attributes['id'].value
        cfg_obj = SiteConfig(sitenode)
        configs[siteid] = cfg_obj
        
    CONFIGS = configs

def load_module(name):
    try:
        __import__(name)
        return sys.modules[name]
    except:
        logging.exception('extractor: failed to load module %s' % name)
        return None

def update_site(siteid):
    config = get_config(siteid)
    data = None

    for module, params in config.get_processors():
        logging.info('extractor: site %s - executing %s' % (siteid, module))
        processor = load_module(module)
        data = processor.process(data, config.siteid, **params)

        if data == None:
            logging.error('extractor: site %s - execution of %s failed' % (siteid, module))
            return None

        if data == []:
            logging.info('extractor: site %s - stops extracting after module %s' % (siteid, module))
            return []

    return data
