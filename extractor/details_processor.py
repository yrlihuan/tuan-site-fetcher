from sgmllib import SGMLParser

structural_tags = ['ul', 'ol', 'li']
format_tags = ['em', 'strong', 'dfn', 'code', \
               'samp', 'kbd', 'var', 'cite', \
               'tt', 'i', 'b', 'big', 'small']
header_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']


class DetailsExtractor(SGMLParser):
    def __init__(self):
        SGMLParser.__init__(self)
        self.details = ''

    def handle_data(self, data):
        print 'handle_data: ' + data

    def handle_endtag(self, tag, method):
        print 'handle_endtag: ' + tag + ' ' + method
        
    def handle_starttag(self, tag, method, attrs):
        print 'handle_starttag: %s, %s, %s' % (tag, method, attrs)

    def unknown_starttag(self, tag, attrs):
        print 'unknown_starttag: %s, %s' % (tag, attrs)

    def unknown_endtag(self, tag):
        print 'unknown_endtag: %s' % tag




