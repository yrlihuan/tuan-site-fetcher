# coding=utf-8

"""
Help find information in a groupon web page.
"""

import sys
import os.path
import re
import urlparse
import urllib2
import imageutil

CURRENTDIR = os.path.dirname(__file__)
sys.path.append(os.path.join(CURRENTDIR, '..'))
from modules import BeautifulSoup

SITE_CONFIGS = os.path.join(CURRENTDIR, 'keywords.xml')
CITIES_LIST = os.path.join(CURRENTDIR, 'cities.xml')

TAG_DISCOUNT = 'discount'
TAG_ORIGINAL = 'original'
TAG_SAVE = 'save'
TAG_PRICE = 'price_now'
TAG_LOCATION = 'location'
TAG_ITEMS = 'items'
TAG_TITLE = 'title'
TAG_IMAGE = 'image'
TAG_CURRENCY = 'currency'
TAG_CITY = 'city'
TAG_DETAILS = 'details'

DIGITS_PATTERN = re.compile(u'\d+(\.\d+)?')
MARKUP_CHAR = re.compile(u'&#\d+;')
EMPTY_PATTERN = re.compile('\A\s*\Z')

DETAILS_KEYWORDS = [u'地址', u'电话', u'本单', u'详情', u'介绍', u'预订', u'预约', u'快递', u'路线', u'交通', u'截至']

class KeywordsSet(object):
    def __init__(self):
        self.attrs = []
        self.__keyset = {}

    def add(self, name, keyword):
        if name not in self.__keyset:
            self.__keyset[name] = set()
            self.attrs.append(name)

        keywordset = self.__keyset[name]
        if keyword not in keywordset:
            keywordset.add(keyword)

    def get(self, attr):
        return self.__keyset.get(attr)

class AnalyzeResult(object):
    def __init__(self):
        self.site_config = ''
        self.site = None
        self.error = None
        self.warnings = []
        self.info_paths = {}
        self.info = {}

class Analyzer(object):
    siteconfigs = None
    cities = None

    @staticmethod
    def __ensure_class_init():
        if not Analyzer.siteconfigs:
            Analyzer.siteconfigs = BeautifulSoup.BeautifulSoup(open(SITE_CONFIGS, 'r'))

        if not Analyzer.cities:
            cities = {}
            cities_config = BeautifulSoup.BeautifulSoup(open(CITIES_LIST, 'r'))

            cities_list = cities_config('city')
            for city in cities_list:
                cities[city.text] = city['id']

            Analyzer.cities = cities

    def __call__(self, markup, site=None):
        if not isinstance(markup, str) and hasattr(markup, 'read'):
            markup = markup.read()
        
        Analyzer.__ensure_class_init()
        self.markup = markup
        self.soup = BeautifulSoup.BeautifulSoup(markup)
        self.site = site

        result = AnalyzeResult()
        result.site = self.site

        self._get_discount_info(result)
        if result.error:
            return result

        self._get_groupon_title(result)
        if result.error:
            return result

        self._get_details(result)
        self._try_get_pic(result)

        return result

    def _get_discount_info(self, result):
        """
        this method tries to extract the following information from the html:
        currency mark,
        discount,
        discoutned price,
        items sold
        """

        # first, try to find a node in html file which contains info such as
        # discount and count of sold items
        configs = self.siteconfigs('site')

        node = None
        for config in configs:
            keywords = KeywordsSet()
            if self.site and not re.compile(config['pattern']).search(self.site):
                continue

            for attr in config.childGenerator():
                if isinstance(attr, BeautifulSoup.Tag) and attr.string and len(attr.string) > 0: # skip invalid or empty values
                    keywords.add(attr.name, attr.string)

            candidates = self._find_node(self.soup, keywords)
            if candidates:
                result.site_config = config['id']
                break 

        if not candidates:
            result.error = 'can not find node containing discount info'
            return

        # $$ for now, only consider the first node $$
        node = candidates[0]

        # the node we got usually contains 1k or so chars.
        # use a search & match method to extract discount info
        key_attrs = [TAG_CURRENCY, TAG_ORIGINAL, TAG_SAVE, TAG_DISCOUNT]
        config = self.siteconfigs.find('site', attrs={'id' : result.site_config})

        keywords = KeywordsSet()
        for attr in config.childGenerator():
            if isinstance(attr, BeautifulSoup.Tag) and attr.string and len(attr.string) > 0: # skip invalid or empty values
                if attr.name in key_attrs:
                    keywords.add(attr.name, attr.string)

        tb_node = self._find_node(node, keywords)[0]
        if not tb_node:
            raise Exception()

        discount_info = self._extract_using_discount(tb_node, keywords)
        if not discount_info:
            discount_info = self._extract_based_on_structure(tb_node, keywords)

        if not discount_info:
            result.error = 'can not parse discount info from markup'
            return result

        for tag in discount_info:
            result.info_paths[tag] = self.soup.get_path(discount_info[tag])
            result.info[tag] = self._convert_to_number(discount_info[tag])

        return result

    def _get_groupon_title(self, result):
        # find the groupon product's title
        # here we assume:
        # title appears before the original price tag
        # title is longer than 20 chars
        # title contains chinese character '元'

        original = 0
        current = 0
        if TAG_ORIGINAL not in result.info:
            result.error = 'discount info doesn\'t contain original price. can not search for title'
            return
        else:
            original = result.info[TAG_ORIGINAL]

        if TAG_SAVE in result.info:
            current = original - result.info[TAG_SAVE]
        elif TAG_DISCOUNT in result.info:
            current = original * result.info[TAG_DISCOUNT]
        elif TAG_PRICE in result.info:
            current = result.info[TAG_PRICE]
        else:
            result.error = 'can not get current price based on discount info'
            return

        # current_str = '%d' % (current)
        # original_str = '%d' % (original)
        yuan_str = u'元'

        original_node = self.soup.get_node(result.info_paths[TAG_ORIGINAL])
        for elem in original_node.previousGenerator():
            if not isinstance(elem, BeautifulSoup.NavigableString) or len(elem) < 15 or self._is_empty(elem):
                continue

            if elem.find(yuan_str) >= 0:
                result.info_paths[TAG_TITLE] = self.soup.get_path(elem)
                result.info[TAG_TITLE] = elem
                return

        result.error = 'can not find title'

    def _get_details(self, result):
        # get the node containing detail info
        # the node must be a sibling of one of the title node's ancestor
        nodes = []
        for info in result.info_paths:
            if info != TAG_TITLE:
                nodes.append(self.soup.get_node(result.info_paths[info]))

        node = self._get_ancestor_of(nodes)
        details_node = None

        # the node contains title and discount info
        while node != self.soup:
            for n in node.nextSiblingGenerator():
                if self._is_details_node(n):
                    details_node = n
                    break

            if details_node:
                break

            for n in node.previousSiblingGenerator():
                if self._is_details_node(n):
                    details_node = n
                    break

            if details_node:
                break

            node = node.parent

        if details_node:
            result.info[TAG_DETAILS] = details_node.text
            result.info_paths[TAG_DETAILS] = self.soup.get_path(details_node)
        else:
            result.warnings.append('Does not find details node')
            

    def _try_get_pic(self, result):

        tried_images = []
        title_node = self.soup.get_node(result.info_paths[TAG_ORIGINAL])

        node = title_node.parent
        while node != self.soup:
            imgs = node.findAll('img')
            for img in imgs:
                if img in tried_images:
                    continue

                imgurl = None
                if img.has_key('src'):
                    imgurl = img['src']
                elif img.has_key('lazysrc'):
                    imgurl = img['lazysrc']

                if imgurl and imgurl != '' and self._is_product_image(imgurl):
                    result.info_paths[TAG_IMAGE] = self.soup.get_path(img)
                    result.info[TAG_IMAGE] = urlparse.urljoin('http://' + self.site, imgurl)
                    return

                tried_images.append(img)

            node = node.parent
        
        result.warnings.append('can not find product image')

    def _find_node(self, root, keywords):
        # This function is used to find a node in the html file that contains the keywords
        # It works as follows:
        # 1. find the node contains the first keyword(s).
        # 2. start from the node found in step(1), try to match all the attributes under
        #    the node. If it doesn't match all the keywords, go to its parent until a match
        #    is found.
        # 3. for all the matches found in step(2), resolve duplicated ones.

        attrs = keywords.attrs

        # step 1: find seed nodes
        seeds = []
        for firstkey in keywords.get(attrs[0]):
            match = re.compile(firstkey)
            seeds += root.findAll(text=match)

        # step 2: find a match from seeds and their parents
        candidates = []
        for seed in seeds:
            current_node = seed
            prev_node = None
            attrs = keywords.attrs
            matched_attrs = [True] + ([False] * (len(attrs) - 1))

            while True:
                # the node is the leap of the tree, go to its parent directly
                if not isinstance(current_node, BeautifulSoup.Tag):
                    prev_node = current_node
                    current_node = current_node.parent
                    continue

                for attr_ind in range(1, len(attrs)):
                    if matched_attrs[attr_ind]:
                        continue

                    find_match_for_attr = False
                    for allowed_keyword in keywords.get(attrs[attr_ind]):
                        match = re.compile(allowed_keyword)
                        if self._find_match_under_node(match, current_node, prev_node):
                            find_match_for_attr = True
                            break

                    # if find a match for a certain attr, then go to next attr.
                    # otherwise stop matching and go to parent directly
                    if find_match_for_attr:
                        matched_attrs[attr_ind] = True
                    else:
                        break

                matched_for_all_attrs = True
                for match_for_attr in matched_attrs:
                    if not match_for_attr:
                        matched_for_all_attrs = False
                        break

                # find a match!
                if matched_for_all_attrs:
                    candidates.append(current_node)
                    break

                if current_node != root:
                    prev_node = current_node
                    current_node = current_node.parent
                else:
                    prev_node = None
                    current_node = None
                    break

        # step 3: resolve duplications
        # if a is a matched node, then any of a's parent is matched too.
        # it's possible if one of the seed leads to no direct solution but
        # to a node that is a solution node's parent.
        match_results = []
        for nodex in candidates:
            duplication = False

            for nodey in candidates:
                if nodex != nodey and self._is_parent_of(nodex, nodey):
                    duplication = True
                    break

            if not duplication:
                match_results.append(nodex)

        return match_results

    def _extract_using_discount(self, node, keywords):
        # this function helps extract price/discount using the following rules
        # it uses following assumptions to find the needed information:
        # 1. discount = price / original_price * 10 (chinese concept '折')
        # 2. saved = original_price - price
        # 3. 0 <= discount <= 10
        # 4. discount is usually at precision of 1~3 decimals
        # 5. no strings (after spaces removed) are longer than 10
        # 6. price/original_price may be clost to keyword['currency']
        # 7. discount is close to chinese character '折'

        price_candidates = []
        discount_candidates = []

        discount_ch = u'折'
        currency_marks = keywords.get('currency')

        for c in node.recursiveChildGenerator():
            
            # process only strings
            if not c or not isinstance(c, BeautifulSoup.NavigableString) or self._is_empty(c):
                continue
                
            # skip long strings, (5)
            if len(c) > 15:
                continue

            # does it contain any digits?
            number = self._convert_to_number(c)
            if number == None:
                continue

            pair = (number, c)
            # could this be the discount value?
            if number < 10 and len(str(number)) <= 4: # rule (3) and (4)
                find_currency_mark = False # rule (6): if True, this is not discount
                for mark in currency_marks:
                    if c.find(mark) >= 0:
                        find_currency_mark = True

                if not find_currency_mark:
                    discount_candidates.append(pair)

            # could this be the price?
            if c.find(discount_ch) < 0: # rule (7)
                price_candidates.append(pair)

        # use rule (1) & (2) to check if the extracted values are valid
        tags = None
        if len(discount_candidates) == 1:
            discount_info = discount_candidates[0]

            # the discount info is duplicated in price info candidates, remove it
            if len(price_candidates) == 3 and discount_info in price_candidates:
                price_candidates.remove(discount_info)

            # we are lucky if only 2 price candidates exist
            # it must be an original_price plus a discounted_price/saved_money
            if len(price_candidates) == 2:
                p1 = price_candidates[0][0]
                p2 = price_candidates[1][0]
                discount = discount_info[0]
                tags = self._match_for_discount(p1, p2, discount)

        if tags:
            return {tags[0] : price_candidates[0][1],
                    tags[1] : price_candidates[1][1],
                    tags[2] : discount_info[1]}
        else:
            return None

    def _extract_based_on_structure(self, node, keywords):

        # this function extracts discount info based on the assumption that
        # the html file contains a table like structure as a container for
        # all the discount info. Usually, the table is like:
        # +-------------+------------+---------+
        # |  old price  |  discount  |  saved  |
        # +-------------+------------+---------+
        # |  $100       |  40%       |  $40    |
        # +-------------+------------+---------+
        # or
        # +-------------+--------+
        # |  old price  |  $100  |
        # +-------------+--------+
        # |  discount   |  40%   |
        # +-------------+--------+
        # |  saved      |  $40   | 
        # +-------------+--------+
        #
        # in html file, the actually presentation may be:
        # <table>
        #   <tr> <td>old price</td> <td>discount</td>   <td>saved</td> </tr>
        #   <tr> <td>$100</td>      <td>40%</td>        <td>$40</td> </tr>
        # </table>
        # or
        # <table>
        #   <tr>    <td>old price</td>  <td>$100</td>   </tr>
        #   <tr>    <td>discount</td>   <td>40%</td>    </tr>
        #   <tr>    <td>saved</td>      <td>$40</td>    </tr>
        # </table>
        # this function try to utilize these information to find the needed info

        key_attrs = [TAG_DISCOUNT, TAG_ORIGINAL, TAG_SAVE]
        elems = []
        found_key_attr = False
        found_two_attrs = False

        # push elems in the markup into elems array
        # in scheme 1: result is ['original', 'discount', 'saved', 100, 40, 100]
        # in scheme 2: result is ['original', 100, 'discount', 40, 'saved', 100]
        for c in node.recursiveChildGenerator():

            # process only strings
            if not c or not isinstance(c, BeautifulSoup.NavigableString) or self._is_empty(c):
                continue

            attr_found = None
            for attr in key_attrs:
                keys = keywords.get(attr)
                if keys:
                    for key in keys:
                        if c.find(key) >= 0:
                            found_key_attr = True
                            attr_found = attr
                            break

                if attr_found:
                    break

            if found_key_attr:
                if attr_found:
                    found_two_attrs = True
                    elems.append(attr_found)
                    continue

                number = self._convert_to_number(c)
                if number != None:
                    elems.append((number, c))
                    continue

                elems.append(None)

        # only one key attr is found. give up trying
        if not found_two_attrs:
            return None

        # the first element is a string, check from the 2nd elem
        scheme = 0
        for elem in elems[1:]:
            if not elem:
                continue
    
            if isinstance(elem, tuple):
                scheme = 2
                break
            else:
                scheme = 1
                break

        result = {}
        if scheme == 1:
            tags = []
            numbers = []

            for elem in elems:
                if isinstance(elem, tuple):
                    numbers.append(elem)
                else:
                    tags.append(elem)


            ind = 0
            indrange = min(len(tags), len(numbers))
            
            for ind in range(0, indrange):
                if tags[ind]:
                    result[tags[ind]] = numbers[ind][1]
        else:
            tag = None

            for elem in elems:
                if not elem:
                    continue

                if isinstance(elem, tuple):
                    if tag:
                        result[tag] = elem[1]
                        tag = None
                else:
                    if not tag:
                        tag = elem
                    else:
                        raise Exception()

        return result

    def _is_product_image(self, image_url):
        if isinstance(image_url, unicode):
            image_url = image_url.encode('utf8')

        while image_url[0:3] == '/..' or image_url[0:3] == '../':
            image_url = image_url[3:]

        image_url = urlparse.urljoin('http://' + self.site, image_url)
        addr = urlparse.urlparse(image_url)
        if addr.netloc == '':
            return False

        try:
            response = urllib2.urlopen(image_url)
            length_str = response.info().getheader('Content-Length')
            if length_str:
                length = int(length_str)
            else:
                length = None

            if length and length < 15000: # assume that any product image is larger than 15k
                return False

            if length and length > 100000: # assume that any image larger than 100k are product image
                return True

            image = imageutil.Image(response)
            image_type = image.type()
            width, height = image.dimensions()
            ratio = float(width) / float(height)

            if image_type != 'UNKNOWN':
                return width > 250 and height > 250 and ratio < 2 and ratio > 0.5
            else:
                return False

        except Exception, ex:
            print ex
            return False

    def _is_details_node(self, node):
        if not isinstance(node, BeautifulSoup.Tag):
            return False

        html_text = node.text
        count = 0

        for keyword in DETAILS_KEYWORDS:
            if html_text.find(keyword) >= 0:
                count += 1

        return count >= 3

    def _find_depth(self, node, root):
        depth = 0
        while node != root:
            node = node.parent
            depth += 1

        return depth

    def _is_parent_of(self, node, child):
        while child != None and child != node:
            child = child.parent

        return child == node

    def _get_ancestor_of(self, nodes):
        paths = []
        for node in nodes:
            paths.append(self.soup.get_path(node))

        path_prefix = paths[0]
        for path in paths[1:]:
            pos = 0
            l1 = len(path_prefix)
            l2 = len(path)
            while pos < l1 and pos < l2 and path[pos] == path_prefix[pos]:
                pos += 1

            path_prefix = path_prefix[:pos]

        last_slash_pos = path_prefix.rindex('/')
        return self.soup.get_node(path_prefix[0:last_slash_pos])

    def _find_match_under_node(self, match, node, searched_child):
        if match.search(node.text):
            return True
        else:
            return False

    def _match_for_discount(self, p1, p2, discount):
        # take 3 values as input, try to find a match of discount value and prices
        # the return value is a tuple containing the matched tag for the three arguments
        if p1 < p2:
            p1, p2 = p2, p1
            switched = True
        else:
            switched = False

        for precision in (0.1, 0.5):
            if abs(((p1 - p2) / p1) * 10 - discount) < precision:
                if switched:
                    return (TAG_SAVE, TAG_ORIGINAL, TAG_DISCOUNT)
                else:
                    return (TAG_ORIGINAL, TAG_SAVE, TAG_DISCOUNT)
            elif abs((p2 / p1) * 10 - discount) < precision:
                if switched:
                    return (TAG_PRICE, TAG_ORIGINAL, TAG_DISCOUNT)
                else:
                    return (TAG_ORIGINAL, TAG_PRICE, TAG_DISCOUNT)

        return None

    def _convert_to_number(self, s):
        s = MARKUP_CHAR.sub('', s) # remove characters like '&#165;'

        match = DIGITS_PATTERN.search(s)
        if match:
            return float(s[match.start():match.end()])
        else:
            return None

    def _is_empty(self, s):
        return EMPTY_PATTERN.match(s) != None

