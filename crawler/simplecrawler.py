"""
simplecrawler.py
A crawler based on BeautifulSoup.
"""

import sys
import os.path
import urllib2
import urlparse
import re
import traceback
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from modules import BeautifulSoup
from crawler import policy

OUTER_SEPARATOR = '=]%'
INNER_SEPARATOR = '[=%'

class WebPage(object):
    def __init__(self, url, parent, depth, text='', visited=False):
        self.url = url
        self.depth = depth
        self.parent = parent
        self.visited = visited
        self.content = None

        if not parent:
            self.linktext = text
        else:
            self.linktext = parent.linktext + u'/' + text

    def __str__(self):
        return 'Visited: ' + str(self.visited) + '\tDepth: ' + str(self.depth) + '\tURL: ' + self.url

    def clone(self):
        page = WebPage(None, None, None)
        for attr in vars(self):
            setattr(page, attr, getattr(self, attr))

        return page

class CrawlerQueue(object):
    def __init__(self):
        self.__pages_dictionary = dict()
        self.__level_list = []
        self.__level_pos = []
        self.__levels = 0

    def serialize(self):
        data = ''
        for level in self.__level_list:
            for page in level:
                if hasattr(page, 'ignoreparams'):
                    continue

                depth_str = str(page.depth)

                if page.visited:
                    visited_str = '1'
                else:
                    visited_str = '0'

                link_parts = page.linktext.split('/')
                link_str = ''
                for text in link_parts:
                    if len(text) > 5:
                        text = text[0:4]

                    link_str += '/' + text

                data += page.url + INNER_SEPARATOR + \
                        link_str + INNER_SEPARATOR + \
                        depth_str + INNER_SEPARATOR + \
                        visited_str + OUTER_SEPARATOR

        return data

    @classmethod
    def deserialize(cls, data):
        queue = cls()
        items = data.split(OUTER_SEPARATOR)

        for item in items:
            if item == '':
                continue

            fields = item.split(INNER_SEPARATOR)
            url = fields[0]
            linktext = fields[1]
            depth = int(fields[2])
            visited = fields[3] == '1'

            page = WebPage(url, None, depth, linktext, visited)
            queue.insert(page)

        return queue

    def has(self, url):
        return url in self.__pages_dictionary

    def insert(self, webpage):
        if self.has(webpage.url):
            raise Exception('Double insertion for URL: %s' % webpage.url)
        
        self.__pages_dictionary[webpage.url] = webpage

        level = webpage.depth
        self._ensure_level(level)
        self.__level_list[level].append(webpage)

    def reactivate(self, webpage, level):
        if not self.has(webpage.url):
            raise Exception('URL not found: %s' % webpage.url)

        if not webpage.visited:
            raise Exception('webpage do not need reactivation: %s' % webpage.url)

        newpage = webpage.clone()
        newpage.visited = False
        newpage.depth = level

        self.__pages_dictionary[newpage.url] = newpage

        self._ensure_level(level)
        self.__level_list[level].append(newpage)

    def get(self, url):
        return self.__pages_dictionary[url]

    def get_next(self):
        l = self.__levels - 1
        while l >= 0:
            pages = self.__level_list[l]
            pos = self.__level_pos[l]
            count = len(pages)

            while pos < count and pages[pos].visited:
                pos += 1

            if pos < count:
                self.__level_pos[l] = pos + 1
                return pages[pos]
            else:
                l -= 1

        return None

    def _ensure_level(self, level):
        while level >= self.__levels:
            self.__level_list.append([])
            self.__level_pos.append(0)
            self.__levels += 1

class SimpleCrawler(object):
    def __init__(self, policy, data=None):
        self.policy = policy
        self.initialize_queue(data)

    def verify_url(self, url):
        parseresult = urlparse.urlparse(url)
        if parseresult.scheme != 'http':
            return False
        
        domainmatch = False

        if len(self.policy.domains) == 0:
            domainmatch = True

        for domain in self.policy.domains:
            if isinstance(domain, basestring) and parseresult.netloc == domain:
                domainmatch = True
                break
            elif hasattr(domain, 'match') and domain.match(parseresult.netloc):
                domainmatch = True
                break

        if not domainmatch:
            return False

        patternmatch = False
        path = parseresult.path

        if path == '':
            path = '/'

        if len(self.policy.patterns) == 0:
            patternmatch = True

        for pattern in self.policy.patterns:
            if hasattr(pattern, 'match') and pattern.match(path):
                patternmatch = True
                break

        return patternmatch

    def verify_count(self, count):
        return self.policy.maximum_pages == 0 or count < self.policy.maximum_pages

    def verify_depth(self, depth):
        return self.policy.maximum_depth == 0 or depth + 1 < self.policy.maximum_depth

    def initialize_queue(self, data):
        if data:
            queue = CrawlerQueue.deserialize(data)
        else:
            queue = CrawlerQueue()
            for url in self.policy.starturls:
                page = WebPage(url, None, 0)
                queue.insert(page)

        self.queue = queue

    def save_crawler_state(self):
        return self.queue.serialize()

    def _similarity_test(self, a, b):
        """
        Test if two markups are actually the same one.
        Returns: True, if a and b are considerably similar
                 False, if a and b are different

        How to test:
        Assume that if two pages are similar if only:
        1. the titles are the same
        2. the links in the page differ by at most 2
        """

        soupa = BeautifulSoup.BeautifulSoup(a)
        soupb = BeautifulSoup.BeautifulSoup(b)

        # test title
        titlea = soupa.find('title')
        titleb = soupb.find('title')
        if titlea.text != titleb.text:
            return False

        # test links
        diff = 0
        linksa = soupa.findAll('a')
        linksb = soupb.findAll('a')

        urls = set([])
        for link in linksa:
            urls.add(link.get('href'))

        for link in linksb:
            url = link.get('href')
            if url not in urls:
                diff += 1
                if diff > 2:
                    return False

        return True

    def crawled_pages(self):
        queue = self.queue
        currentindex = -1

        while True:
            try:
                currentindex = currentindex + 1
                currentpage = queue.get_next()
                if not currentpage or not self.verify_count(currentindex):
                    break

                currentpage.visited = True

                # if this is a parametered address, and if we should ignore it
                urlcomponents = urlparse.urlparse(currentpage.url)
                url_no_params = None
                if urlcomponents.params != '' or urlcomponents.query != '' or urlcomponents.fragment != '':
                    # url_no_params is a special url, which represents all
                    # the parametered pages with the same base address
                    url_no_params = urlparse.urlunparse([urlcomponents.scheme, urlcomponents.netloc, urlcomponents.path, '', 'no_params=True', ''])

                    if queue.has(url_no_params):
                        page_no_params = queue.get(url_no_params)
                        if page_no_params.ignoreparams:
                            continue

                if not currentpage.content:
                    # send HTTP GET request
                    pagecontent = urllib2.urlopen(currentpage.url)
                    real_url = pagecontent.geturl()
                    currentpage.content = pagecontent.read()

                    # check if the link is redirected. if yes, we need add also the redirected page into the collection
                    if real_url != currentpage.url:
                        if queue.has(real_url):
                            redirected = queue.get(real_url)
                            redirected.visited = True
                            redirected.content = currentpage.content
                        else:
                            redirected = currentpage.clone()
                            redirected.url = real_url
                            queue.insert(redirected)

                        currentpage = redirected

                # if this is a parametered address, check whether we should ignore the parameters in future
                if url_no_params:
                    if not queue.has(url_no_params):
                        page_no_params = currentpage.clone()
                        page_no_params.url = url_no_params
                        page_no_params.ignoreparams = None # ignoreparams is a tri-state var. True, False, None
                        queue.insert(page_no_params)
                    else:
                        page_no_params = queue.get(url_no_params)
                        if page_no_params.ignoreparams == None: # it could be None or False
                            markup_old = page_no_params.content
                            markup_new = currentpage.content
                            # logging.info('similarity test')
                            page_no_params.ignoreparams = self._similarity_test(markup_old, markup_new)
                            # logging.info(page_no_params.ignoreparams)

                        if page_no_params.ignoreparams:
                            continue

            except Exception, e:
                logging.exception('Exception caught when accessing page ' + currentpage.url)
                # traceback.print_exc()
                continue


            # add links to queue
            soup = BeautifulSoup.BeautifulSoup(currentpage.content)
            if self.verify_depth(currentpage.depth): # process the links only if the depth does not exceed the maximum
                links = soup.findAll('a')
                linkdepth = currentpage.depth + 1

                for link in links:
                    link_url = link.get('href')

                    if link_url == None or link_url == '':
                        continue

                    link_url_full = urlparse.urljoin(currentpage.url, link_url)

                    if queue.has(link_url_full):
                        oldpage = queue.get(link_url_full)
                        if oldpage.depth > linkdepth:
                            queue.reactivate(oldpage, linkdepth)
                    elif self.verify_url(link_url_full):
                        newpage = WebPage(link_url_full, currentpage, linkdepth, link.text)
                        queue.insert(newpage)


            logging.info('Crawler: Page crawled! %s' % currentpage.url)
            yield currentpage


