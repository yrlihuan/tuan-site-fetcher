# coding=utf-8

import os.path
import analyzer
import re
import os
import BeautifulSoup
import webbrowser

test_htmls_dir = 'C:\\testresult\\various_sites'

essential_tags = ['price_now', 'original', 'discount', 'save', 'image', 'title']

output_header = u"""
<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    </head>"""

output_tailer = u"""
</html>
"""

output_site = u"""
<h1>%(site)s</h1>
<p>%(title)s</p>
<table>
    <tr>
        <th>原价</th>
        <th>现价</th>
        <th>折扣</th>
        <th>节省</th>
    </tr>
    <tr>
        <th>%(original)s</th>
        <th>%(price_now)s</th>
        <th>%(discount)s</th>
        <th>%(save)s</th>
    </tr>
</table>

<img src='%(image)s'/>
"""

def test_soup_search(html='www.nuomi.com.html'):
    site_html_file = os.path.join(test_htmls_dir, html)

    siteconfigs = BeautifulSoup.BeautifulSoup(open(analyzer.SITE_CONFIGS, 'r'))
    configs = siteconfigs('site')
    
    markup = open(site_html_file, 'r')
    soup = BeautifulSoup.BeautifulSoup(markup)

    for config in configs:
        for attr in config.childGenerator():
            if hasattr(attr, 'name') and attr.string and len(attr.string) > 0:
                match = re.compile(attr.string)
                if soup.find(text=match):
                    print 'find! ' + unicode.encode(attr.string, 'gb2312')
                else:
                    print 'not found! ' + attr.string
    

def test_dianping(args=None):
    site_html_file = os.path.join(test_htmls_dir, 't.dianping.com.html')
    
    markup = open(site_html_file, 'r')
    ana = analyzer.Analyzer()
    return ana(markup, site_html_file)

def test_nuomi(args=None):
    site_html_file = os.path.join(test_htmls_dir, 'www.nuomi.com.html')
    
    markup = open(site_html_file, 'r')
    ana = analyzer.Analyzer()
    return ana(markup, site_html_file)

def test_site(html):
    site_html_file = os.path.join(test_htmls_dir, html)
    
    markup = open(site_html_file, 'r')
    ana = analyzer.Analyzer()
    return ana(markup, html[0:-5])

def test_various_sites(args=None):
    html_files = os.listdir(test_htmls_dir)
    html_output_path = 'c:\\testresult\\test_results.html'

    html_output = open(html_output_path, 'w')
    html_output.write(output_header)

    for f in html_files:
        if f[-4:] != 'html':
            continue

        print '-' * 80

        site = os.path.basename(f)[0:-5]

        site_html_file = os.path.join(test_htmls_dir, f)
        markup = open(site_html_file, 'r')
        ana = analyzer.Analyzer()

        result = ana(markup, site)
        markup.close()
        if result.error:
            print 'Failed! ' + site_html_file + ' ' + result.error
        else:
            print 'Succeed! ' + site_html_file

            if len(result.warnings):
                print 'Warnings: ' + str(result.warnings)
            # print_results(result)

            site_data = {}
            site_data['site'] = result.site
            site_data['error'] = result.error
            site_data['warnings'] = result.warnings

            for tag in result.info:
                site_data[tag] = result.info[tag]

            for tag in essential_tags:
                if tag not in site_data:
                    site_data[tag] = None

            site_markup = output_site % site_data
            html_output.write(site_markup.encode('utf8'))

    html_output.write(output_tailer)
    html_output.close()

    webbrowser.open('file://' + html_output_path)

def print_results(result):
    for tag in result.info_paths:
        print tag + ': ' + str(result.info[tag])

def run_test(test, verbose=False, args=None):
    print '-' * 60
    print 'Starting test ' + test.func_name
    result = test(args)

    if result:
        print 'Succeed! ' + test.func_name
    else:
        print 'Failed! ' + test.func_name

    if verbose:
        print result

    print 'Test ended ' + test.func_name

if __name__ == '__main__':
    run_test(test_various_sites)

