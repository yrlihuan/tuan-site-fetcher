#!/usr/bin/python

import os.path
import sys
import os

APPLIST = 'applist'
APPYAML = 'app.yaml'
APPCFG = '/usr/bin/appcfg.py'
USERNAME = 'tuanappdev@gmail.com'

def update_app(appdir, appid):
    command = '%s --email=%s --insecure --application=%s update %s' % (APPCFG, USERNAME, appid, appdir)
    print '*' * 30
    print command
    return os.system(command)

def update_all():
    app_dirs = ['admin_site', 'analyzer_site', 'user_site']

    failed = False
    for d in app_dirs:
        app_list = open(os.path.join(d, APPLIST), 'r')

        for appid in app_list:
            appid = appid.replace('\n', '')
            if update_app(d, appid):
                failed = True

    if not failed:
        print 'All sites updated successfully!'
    else:
        print 'Error happens when updating!'

if __name__ == '__main__':
    update_all()
