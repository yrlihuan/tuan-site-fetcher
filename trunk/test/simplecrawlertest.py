import urlparse
import os.path
import sys
import urllib2

CURRENTDIR = os.path.dirname(__file__)
sys.path.append(os.path.join(CURRENTDIR, '..'))
from crawler import simplecrawler
from crawler.policy import CrawlerPolicy
import testutil

output_dir = os.path.join(CURRENTDIR, 'crawledpages')

def test_similarity(**args):
    similar_set = [('http://www.nuomi.com/subscribe/add?area=2700010000', 'http://www.nuomi.com/subscribe/add?area=3200010000'),
                   ('http://www.nuomi.com/zhengzhou/maibaobao.html?ref=hometitle', 'http://www.nuomi.com/zhengzhou/maibaobao.html?ref=homebtn'),
                   ('http://www.nuomi.com/beijing/maibaobao.html?ref=hometitle', 'http://www.nuomi.com/beijing/maibaobao.html?ref=homeimage')]

    unsimilar_set = [('http://www.nuomi.com/changecity?areaCode=1000010000','http://www.nuomi.com/changecity?areaCode=600110000')]

    policy = CrawlerPolicy()
    crawler = simplecrawler.SimpleCrawler(policy)

    for urla, urlb in similar_set:
        contenta = urllib2.urlopen(urla).read()
        contentb = urllib2.urlopen(urlb).read()
        similarity = crawler._similarity_test(contenta, contentb)
        testutil.assert_eq(similarity, True)

    for urla, urlb in unsimilar_set:
        contenta = urllib2.urlopen(urla).read()
        contentb = urllib2.urlopen(urlb).read()
        similarity = crawler._similarity_test(contenta, contentb)
        testutil.assert_eq(similarity, False)

    return True

def test_yoka_ajax(**args):
    output_sub_dir = 'yoka'

    output_path = os.path.join(output_dir, output_sub_dir)
    if not os.path.isdir(output_path):
        os.mkdir(output_path)

    policy = CrawlerPolicy()
    policy.maximum_depth = 2
    policy.maximum_pages = 20
    policy.domains.append('tuan.yoka.com')
    policy.starturls.append('http://tuan.yoka.com/')
    
    crawler = simplecrawler.SimpleCrawler(policy)
    index = 0
    for page in crawler.crawled_pages():
        print page
        parseresult = urlparse.urlparse(page.url)
        filepath = os.path.join(output_dir, output_sub_dir, str(index) + '.html')
        f = open(filepath, 'w')
        f.write(page.content)
        f.close()

        index = index + 1

def test_nuomi(**args):
    policy = CrawlerPolicy()
    policy.maximum_depth = 2
    policy.maximum_pages = 20
    policy.domains.append('www.nuomi.com')
    policy.starturls.append('http://www.nuomi.com/beijing')
    
    crawler = simplecrawler.SimpleCrawler(policy)
    for page in crawler.crawled_pages():
        print page

def test_various_sites(**args):
    print 'test_various_sites'
    output_sub_dir = 'various_sites'

    output_path = os.path.join(output_dir, output_sub_dir)
    if not os.path.isdir(output_path):
        os.mkdir(output_path)
    
    sites = ['http://www.nuomi.com/',
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
             ]

    for site in sites:
        print site
        domain = urlparse.urlparse(site).netloc

        policy = CrawlerPolicy()
        policy.maximum_depth = 1
        policy.maximum_pages = 1
        policy.domains = [domain]
        policy.starturls = [site]

        crawler = simplecrawler.SimpleCrawler(policy)

        for page in crawler.crawled_pages():
            print page
            parseresult = urlparse.urlparse(page.url)
            filepath = os.path.join(output_dir, output_sub_dir, domain + '.html')
            f = open(filepath, 'w')
            f.write(page.content)
            f.close()
            break

if __name__ == '__main__':
    # testutil.run_test(test_similarity)
    testutil.run_test(test_various_sites)
    
    raw_input('Enter anything to quit!')
