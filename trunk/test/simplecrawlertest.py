import urlparse
import os.path
import sys

CURRENTDIR = os.path.dirname(__file__)
sys.path.append(os.path.join(CURRENTDIR, '..\\crawler'))
import simplecrawler

output_dir = 'c:\\testresult'

def test_yoka_ajax(args=None):
    print 'test_yoka_ajax'
    output_sub_dir = 'yoka'

    output_path = os.path.join(output_dir, output_sub_dir)
    if not os.path.isdir(output_path):
        os.mkdir(output_path)

    policy = simplecrawler.CrawlerPolicy()
    policy.maximum_depth = 2
    policy.maximum_pages = 20
    policy.domains = set(['tuan.yoka.com'])
    
    crawler = simplecrawler.SimpleCrawler('http://tuan.yoka.com/', policy)
    index = 0
    for page in crawler.crawled_pages():
        print page[0]
        parseresult = urlparse.urlparse(page[0].url)
        filepath = os.path.join(output_dir, output_sub_dir, str(index) + '.html')
        f = open(filepath, 'w')
        f.write(page[1])
        f.close()

        index = index + 1

def test_nuomi(args=None):
    print 'test_nuomi'
    
    policy = simplecrawler.CrawlerPolicy()
    policy.maximum_depth = 2
    policy.maximum_pages = 20
    policy.domains = set(['www.nuomi.com'])
    
    crawler = simplecrawler.SimpleCrawler('http://www.nuomi.com/beijing', policy)
    for page in crawler.crawled_pages():
        print page[0]

def test_aibang(args=None):
    print 'test_aibang'

    policy = simplecrawler.CrawlerPolicy()
    policy.maximum_depth = 2
    policy.maximum_pages = 20
    policy.domains = set(['tuan.aibang.com'])
    
    crawler = simplecrawler.SimpleCrawler('http://tuan.aibang.com/', policy)
    for page in crawler.crawled_pages():
        print page[0]

def test_save_to_file(args=None):
    print 'test_save_to_file'
    output_sub_dir = 'dianping'

    output_path = os.path.join(output_dir, output_sub_dir)
    if not os.path.isdir(output_path):
        os.mkdir(output_path)
    
    policy = simplecrawler.CrawlerPolicy()
    policy.maximum_depth = 3
    policy.maximum_pages = 10
    policy.domains = set(['t.dianping.com'])
    
    crawler = simplecrawler.SimpleCrawler('http://t.dianping.com/', policy)

    index = 0
    for page in crawler.crawled_pages():
        print page[0]
        parseresult = urlparse.urlparse(page[0].url)
        filepath = os.path.join(output_dir, output_sub_dir, str(index) + '.html')
        f = open(filepath, 'w')
        f.write(page[1])
        f.close()

        index = index + 1

def test_various_sites(args=None):
    print 'test_various_sites'
    output_sub_dir = 'various_sites'

    output_path = os.path.join(output_dir, output_sub_dir)
    if not os.path.isdir(output_path):
        os.mkdir(output_path)
    
    sites = set(['http://www.nuomi.com/',
                 'http://t.dianping.com/',
                 'http://www.lashou.com/deal/beijing/14115.html',
                 'http://www.meituan.com/beijing/deal/BJHJX.html',
                 'http://www.24quan.com/',
                 'http://tuan.qq.com/',
                 'http://www.didatuan.com/',
                 'http://www.groupon.cn/BeiJing/BeiJing10434.html',
                 'http://www.manzuo.com/his/meirong__gPXiJyJOgyU.htm',
                 'http://tuan.aibang.com/beijing/caipiao.html',
                 'http://tuan.fantong.com/',
                 'http://t.58.com/',
                 'http://t.58.com/bj/1135',
                 'http://www.jumei.com/',
                 'http://www.ftuan.com/team.php?id=1098',
                 'http://beijing.ayatuan.com/2710',
                 'http://www.haotehui.com/gp-2223.jhtml',
                 'http://shuangtuan.com/',
                 'http://tuan.sohu.com/beijing/life/tuan/zippo.html',
                 'http://tuan.yoka.com/435',
                 'http://www.meilishuo.com/tuan',
                 'http://life.sina.com.cn/tuan/',
                 'http://shequ.soufun.com/g/',
                 'http://tuan.zol.com/289.html',
                 'http://tuan.piao.com/',
                 'http://www.tuanxia.com/deals/shxinren',
                 'http://www.55tuan.com/',
                 'http://www.tuan001.com/',
                 'http://www.kutuan.com/beijing/deal',
                 'http://www.fenpier.com/',
                 'http://tuan.youa.com/',
                 'http://www.tuanweihui.com/g-yinfanxiwayujia.html',
                 'http://www.17mh.com/',
                 'http://www.zhenxi.com/',
                 'http://www.chinaxqg.com/',
                 'http://www.gantuan.com/',
                 'http://www.06.com.cn/',
                 'http://www.xing800.com/getgroupbuy.html?id=20148',
                 'http://shenzhen.gtuan.com/goodslist.php?act=view&g_id=793'
                 ])

    for site in sites:
        print site
        domain = urlparse.urlparse(site).netloc

        policy = simplecrawler.CrawlerPolicy()
        policy.maximum_depth = 1
        policy.maximum_pages = 1
        policy.domains = set([domain])

        crawler = simplecrawler.SimpleCrawler(site, policy)

        for page in crawler.crawled_pages():
            print page[0]
            parseresult = urlparse.urlparse(page[0].url)
            filepath = os.path.join(output_dir, output_sub_dir, domain + '.html')
            f = open(filepath, 'w')
            f.write(page[1])
            f.close()
            break

if __name__ == '__main__':
    test_various_sites()
    
        
