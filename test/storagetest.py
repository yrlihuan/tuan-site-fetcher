import sys
import os.path
import datetime

CURRENTDIR = os.path.dirname(__file__)
sys.path.append(os.path.join(CURRENTDIR, '..\\'))

from modules import storage
from modules.storage import storageimpl

import testutil

def test_storageimpl(**args):
    # Testing creation
    storageimpl.create_or_update('site', 'siteid', siteid='google')
    storageimpl.create_or_update('site', 'siteid', siteid='baidu')

    date = datetime.datetime.now()
    storageimpl.create_or_update('page', 'url', url='www.google.com', siteid='google', updatedate=date, data=u'us', infopage=False)
    storageimpl.create_or_update('page', 'url', url='www.google.com.hk', siteid='google', updatedate=date, data=u'hk', infopage=False)
    storageimpl.create_or_update('page', 'url', url='www.baidu.com', siteid='baidu', updatedate=date, data=u'<html>', infopage=True)
    storageimpl.create_or_update('page', 'url', url='www.bing.com', siteid='bing')

    # Testing query
    qresult = storageimpl.query('site', siteid='google')
    rows = to_array(qresult)
    testutil.assert_eq(len(rows), 1)
    testutil.assert_eq(rows[0].siteid, 'google')

    qresult = storageimpl.query('page', url='www.google.com.hk')
    rows = to_array(qresult)
    testutil.assert_eq(len(rows), 1)
    r = rows[0]
    testutil.assert_eq(r.url, 'www.google.com.hk')
    testutil.assert_eq(r.siteid, 'google')
    testutil.assert_eq(r.updatedate, date)
    testutil.assert_eq(r.data, u'hk')
    testutil.assert_eq(r.infopage, False)

    qresult = storageimpl.query('page', siteid='google')
    rows = to_array(qresult)
    testutil.assert_eq(len(rows), 2)

    qresult = storageimpl.query('page')
    rows = to_array(qresult)
    testutil.assert_eq(len(rows), 4)

    # Testing update
    storageimpl.create_or_update('page', 'url', url='www.bing.com', updatedate=date, data=u'ms', infopage=True)
    qresult = storageimpl.query('page', url='www.bing.com')
    rows = to_array(qresult)
    testutil.assert_eq(len(rows), 1)
    r = rows[0]
    testutil.assert_eq(r.url, 'www.bing.com')
    testutil.assert_eq(r.siteid, 'bing')
    testutil.assert_eq(r.updatedate, date)
    testutil.assert_eq(r.data, u'ms')
    testutil.assert_eq(r.infopage, True)

    qresult = storageimpl.query('page')
    rows = to_array(qresult)
    testutil.assert_eq(len(rows), 4)
    
    # Testing deleting
    storageimpl.delete('site')
    storageimpl.delete('page')
    
    qresult = storageimpl.query('site')
    rows = to_array(qresult)
    testutil.assert_eq(len(rows), 0)
    qresult = storageimpl.query('page')
    rows = to_array(qresult)
    testutil.assert_eq(len(rows), 0)

    return True

def to_array(iterable):
    r = []
    for i in iterable:
        r.append(i)

    return r

if __name__ == '__main__':
    testutil.run_test(test_storageimpl)

    raw_input('Test Ended. Enter any key to continue...')

