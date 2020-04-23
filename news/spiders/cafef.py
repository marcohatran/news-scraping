from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import scrapy
import json
import modules.timeConverter as time

class CafefSpider(CrawlSpider):
    name = "cafef"
    custom_settings = {
        'CONCURRENT_REQUESTS': 100,
        'REACTOR_THREADPOOL_MAXSIZE': 20,
        'LOG_LEVEL': 'INFO',
        'COOKIES_ENABLED': False,
        'RETRY_ENABLED': False,
        'REDIRECT_ENABLED': False,
        'AJAXCRAWL_ENABLED': True,
    }
    allowed_domains = ['cafef.vn', 'sharefb.cnnd.vn']
    start_urls = ['http://cafef.vn/']

    rules = (
        Rule(LinkExtractor(allow_domains=['cafef.vn'], deny_domains=['s.cafef.vn', 'images1.cafef.vn', 'solieu4.cafef.vn','ta.cafef.vn']), callback='parse_item', follow=True),
    )

    def __init__(self, crawlMode='', **kwargs):
        super().__init__(**kwargs)
        self.crawlMode = crawlMode
        if crawlMode is 'update' or crawlMode is '':
            self.crawlMode = 'Update'
        print(self.crawlMode)

        self.articleCount = 0

    def parse_item(self, response):
        article = dict()
        title_arr = response.xpath('//h1[@class="title"]/text()').get()
        if title_arr is not None:
            title = title_arr.strip()
            # get ld_json
            try:
                ld_json = response.xpath('//script[contains(text(),"NewsArticle")]/text()').get()
                ld_json = ld_json
                ld_json = json.loads(ld_json)
                ld_json = time.timestamp_converter(ld_json)
                article.update(ld_json)
            except:
                pass
            # get headline
            article.update({'headline': response.xpath("//meta[@itemprop='headline']/@content").get()})
            # get thumbnail
            image_list = response.xpath('//div/img/@src').getall()
            image_str = str(image_list)
            article.update({'thumbnail': image_str})
            # get meta
            article.update({'type': response.xpath("//head/meta[@property='og:type']/@content").get()})
            article.update({'description': response.xpath("//meta[@name='description']/@content").get()})
            article.update({'keywords': response.xpath("//meta[@name='keywords']/@content").get()})
            article.update({'category': response.xpath("//meta[@property='article:section']/@content").get()})
            article.update({'copyright': response.xpath("//meta[@name='copyright']/@content").get()})
            article.update({'author': response.xpath("//meta[@name='author']/@content").get()})
            article.update({'language': response.xpath("//meta[@name='Language']/@content").get()})
            article.update({'geo_place_name': response.xpath("//meta[@name = 'geo.placename']/@content").get()})
            article.update({'geo_region': response.xpath("//meta[@name = 'geo.region']/@content").get()})
            article.update({'geo_position': response.xpath("//meta[@name = 'geo.position']/@content").get()})
            article.update({'organization': 'Cafef'})
            # get title, link
            link = response.url
            article.update({'title': title, 'link': link})
            article.update({'author': response.xpath("//p[@class='author']/text()").get()})
            # get contents
            content = ''
            for text in response.xpath(
                    '(//div[@class="contentdetail"]/span/p/text())|(//div[@class="companyIntro"]/text())').getall():
                content += text.strip()
            article.update({'content_article': content})
            if content is not None:
                word_count = len(content.split())
                article.update({'word_count': word_count})
            else:
                word_count = -1
                article.update({'word_count': word_count})

            # get likes,comments
            yield scrapy.Request("https://sharefb.cnnd.vn/?urls=" + response.url,
                                 callback=self.parse_interactions,
                                 headers={'Accept': 'application/json, text/javascript, */*; q=0.01',
                                          'Origin': 'https://cafef.vn',
                                          'Referer': response.url,
                                          'Sec-Fetch-Mode': 'cors',
                                          },
                                 meta={'article': article})

            # get relate_url
            relate_url = []
            htags = response.xpath('//div[@class="bg-tit-samecate"]/h4')
            for tag in htags:
                relate_urls = {}
                headline = tag.xpath('a/@title').get()
                url = "https://cafef.vn" + str(tag.xpath('a/@href').extract_first())
                relate_urls.update({'headline': headline, 'url': url})
                relate_url.append(relate_urls)
            article.update({"related_url": str(relate_url)})

    def parse_interactions(self, response):
        str1 = ''
        for text in response.xpath('//text()').getall():
            str1 += text
        list_inter = json.loads(str1)
        dict_inter = dict(list_inter[0])
        del dict_inter['url']
        article = response.meta['article']
        article.update(dict_inter)
        self.logger.info("#%d: Scraping %s", self.articleCount,
                        article.get('link'))
        self.articleCount += 1
        yield article