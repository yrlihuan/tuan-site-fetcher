import urllib2
import os.path
import sys
import logging
from datetime import datetime

CURRENTDIR = os.path.dirname(__file__)
ROOTDIR = os.path.join(CURRENTDIR, '..')
sys.path.append(CURRENTDIR)
sys.path.append(ROOTDIR)

from modules.BeautifulSoup import BeautifulSoup
from modules.BeautifulSoup import Tag
from modules import storage

CONFIG_FILE = os.path.join(CURRENTDIR, 'configs.xml')
CONFIGS = None

class SiteConfig():
    def __init__(self, markup):
        self.siteid = markup['id']
        self.markup = markup

    def get_processors(self):
        processors = self.markup.findAll('processor')

        for processor in processors:
            module = processor['module']
            params = {}
            for n in processor.childGenerator():
                if not isinstance(n, Tag):
                    continue

                params[str(n.name)] = n.text

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
    config_file = open(CONFIG_FILE, 'r')
    config_markup = BeautifulSoup(config_file)
    config_file.close()

    for node in config_markup.findAll('site'):
        siteid = node['id']
        cfg_obj = SiteConfig(node)
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
