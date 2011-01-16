"""
simplecrawler.py
A crawler based on BeautifulSoup.
"""

import sys
import os.path
import urllib2
import urlparse

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from modules import BeautifulSoup

class DoubleInsertionException(Exception):
    def __str__(self):
        return 'DoubleInsertionException'

class CrawlerPolicy(object):
    def __init__(self):
        self.domains = {}
        self.maximum_pages = 0
        self.maximum_depth = 0

class WebPage(object):
    def __init__(self, url, parent, depth):
        self.url = url
        self.depth = depth
        self.parent = parent
        self.visited = False

    def __str__(self):
        return 'Visited: ' + str(self.visited) + '\tDepth: ' + str(self.depth) + '\tURL: ' + self.url

    def clone(self):
        page = WebPage(self.url, self.parent, self.depth)
        page.visited = self.visited
        return page

class WebPageCollection(object):
    def __init__(self):
        self.__pages_dictionary = dict()
        self.__pages_list = list()

    def has(self, url):
        return url in self.__pages_dictionary

    def insert(self, webpage):
        if self.has(webpage.url):
            raise DoubleInsertionException()
        
        self.__pages_dictionary[webpage.url] = webpage
        self.__pages_list.append(webpage)

    def get(self, url):
        return self.__pages_dictionary[url]

    def get_at(self, index):
        return self.__pages_list[index]

    def count(self):
        return len(self.__pages_list)

    def pages(self):
        return self.__pages_list

class SimpleCrawler(object):
    def __init__(self, starturl, policy):
        if isinstance(starturl, set):
            self.starturl = starturl
        else:
            self.starturl = set([starturl])

        self.policy = policy

    def verify_domain(self, url):
        parseresult = urlparse.urlparse(url)
        if parseresult.scheme != 'http':
            return False

        return parseresult.netloc in self.policy.domains

    def verify_count(self, count):
        return self.policy.maximum_pages == 0 or count < self.policy.maximum_pages

    def verify_depth(self, depth):
        return self.policy.maximum_depth == 0 or depth + 1 < self.policy.maximum_depth

    def _set_start_urls(self):
        result = WebPageCollection()

        for url in self.starturl:
            page = WebPage(url, None, 0)
            result.insert(page)

        return result

    def crawled_pages(self):
        pagecollection = self._set_start_urls()
        currentindex = -1
        count = 0

        while True:
            try:
                currentindex = currentindex + 1
                
                if currentindex >= pagecollection.count() or not self.verify_count(count):
                    break

                currentpage = pagecollection.get_at(currentindex)
                if currentpage.visited: # if the page has already been visited (in the case of re-direction), ignore it
                    continue

                pagecontent = urllib2.urlopen(currentpage.url)
                redirected_url = pagecontent.geturl()
                currentpage.visited = True

                # if the page has already been visited, ignore it
                if redirected_url != currentpage.url \
                        and pagecollection.has(redirected_url) \
                        and pagecollection.get(redirected_url).visited:
                            continue
                           
                pagebuffer = pagecontent.read()
                soup = BeautifulSoup.BeautifulSoup(pagebuffer)
                count = count + 1

                # check if the link is redirected. if yes, we need add also the redirected page into the collection
                if redirected_url != currentpage.url:
                    if pagecollection.has(redirected_url):
                        redirected = pagecollection.get(redirected_url)
                        redirected.visited = True
                    else:
                        redirected = currentpage.clone()
                        redirected.url = redirected_url
                        pagecollection.insert(redirected)

                    currentpage = redirected # use the redirected page instead of the original page

            except Exception as e:
                print 'Exception caught when accessing page' + currentpage.url
                print e
                continue

            yield currentpage, pagebuffer

            if self.verify_depth(currentpage.depth): # process the links only if the depth does not exceed the maximum
                links = soup('a')
                linkdepth = currentpage.depth + 1

                for link in links:
                    link_url = link.get('href')

                    if link_url == None or link_url == '':
                        continue

                    link_url_full = urlparse.urljoin(currentpage.url, link_url)

                    if self.verify_domain(link_url_full) and not pagecollection.has(link_url_full):
                        newpage = WebPage(link_url_full, currentpage, linkdepth)
                        pagecollection.insert(newpage)

#        print 'Execution ended!'
#        for page in pagecollection.pages():
#            print page

