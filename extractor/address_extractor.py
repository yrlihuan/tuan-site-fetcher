# coding=utf-8

import logging
from modules.BeautifulSoup import BeautifulSoup
from modules.BeautifulSoup import NavigableString

ADDR_KEYWORDS = [u'市', u'区', \
                 u'街', u'路', u'里', u'弄', u'巷',\
                 u'大厦', u'号', u'层', u'楼', u'室', u'座']
KEYS_REQUIRED = 3

def process(data, siteid):
    """
    Get the address from detailed address info
    """

    for g in data:
        if not hasattr(g, 'addrdetails'):
            continue
        
        details = vars(g).pop('addrdetails')
        markup = BeautifulSoup(details)
        for tag in markup.recursiveChildGenerator():
            if not isinstance(tag, NavigableString):
                continue

            # address should be longer than 5 chars
            if len(tag) < 5:
                continue

            cnt = 0
            found = False
            for key in ADDR_KEYWORDS:
                if key not in tag:
                    continue
                
                cnt += 1
                if cnt >= KEYS_REQUIRED:
                    found = True
                    break
                        
            if found:
                g.address = tag
                break


    return data

