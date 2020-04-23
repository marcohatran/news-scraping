from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import scrapy
import json
import modules.timeConverter as time


class VtvSpider(CrawlSpider):
    name = "vtv.vn"
    allowed_domains = ['vtv.vn', 'sharefb.cnnd.vn']
    start_urls = ['http://vtv.vn/']
    rules = (
        Rule(LinkExtractor(allow_domains=['vtv.vn']), callback='parse_item', follow=True),
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
        title = response.xpath('(//h1[@class="title_detail"]/text())|(//div[@class="infomationdetail clearfix"]/h1/text())').get()
        if title is not None:
            # get ld_json
            ld_json = response.xpath('//head/script[@type="application/ld+json"]/text()').get()
            if ld_json is not None:
                try:
                    ld_json = json.loads(ld_json)
                    ld_json = time.timestamp_converter(ld_json)
                    article.update(ld_json)
                except ValueError:
                    pass
            if 'dateModified' in article.keys():
                dateModified = response.xpath('//meta[@name="pubdate"]/@content').get()
                article.update({'dateModified': time.Vnex_timestamp(dateModified)})
            if 'datePublished' in article.keys():
                datePublished = response.xpath('//meta[@name="lastmod"]/@content').get()
                article.update({'datePublished': time.Vnex_timestamp(datePublished)})
            # get meta
            article.update({'type': response.xpath("//head/meta[@property='og:type']/@content").get()})
            article.update({'description': response.xpath("//head/meta[@name='description']/@content").get()})
            article.update({'keywords': response.xpath("//head/meta[@name='keywords']/@content").get()})
            article.update({'category': response.xpath("//head/meta[@property='article:section']/@content").get()})
            article.update({'copyright': response.xpath("//head/meta[@name='copyright']/@content").get()})
            article.update({'language': response.xpath("//head/meta[@name='Language']/@content").get()})
            article.update({'geo_place_name': response.xpath("//meta[@name = 'geo.placename']/@content").get()})
            article.update({'geo_region': response.xpath("//meta[@name = 'geo.region']/@content").get()})
            article.update({'geo_position': response.xpath("//meta[@name = 'geo.position']/@content").get()})
            article.update({'organization': 'VTV'})
            title = response.xpath('//meta[@property="og:title"]/@content').get()
            link = response.url
            article.update({'title': title, 'link': link})
            # author
            content = ''
            author = ''
            for text in response.xpath('(//p[@class="news-info"]/b/text())|(//p[@class="author"]/text())').getall():
                author += text.strip()
            article.update({'author': author})
            for text in response.xpath(
                    '(//div[@id="entry-body"]/p/text())|(//div[@class="w638 mgl96"]/div[@class="ta-justify"]/p/text())').getall():
                content += text.strip()
            article.update({'content_article': content})
            word_count = len(content.split())
            article.update({'word_count': word_count})
            # get image
            thumbnail = response.xpath('(//div[@class="infomationdetail clearfix"]/img/@src)|(//div[@class="noidung"]/img/@src)|(//div[@type="Photo"]/div/img/@src)|(//figure[@class="LayoutAlbumItem"]/a/img/@src)').getall()
            if thumbnail is not None:
                article.update({'thumbnail': thumbnail})
            else:
                article.update({'thumbnail': '-1'})

            # get relate_url
            relate_url = []
            htags = response.xpath('//div[@class="clearfix pdb20"]/ul/li')
            for tag in htags:
                relate_urls = {}
                headline = tag.xpath('a/@title').get()
                if headline is not []:
                    url = "https://vtv.vn" + str(tag.xpath('a/@href').extract_first())
                    relate_urls.update({'headline': headline, 'url': url})
                    relate_url.append(relate_urls)
                article.update({"related_url": relate_url})
            objectid = response.xpath('//div[@class="aspNetHidden"]/input[@id="hdNewsId"]/@value').get()
            cmt_resquest = 'https://sharefb.cnnd.vn/?urls=http://vtv.vn/news-' + str(objectid) + '.htm'
            yield scrapy.Request(cmt_resquest, callback=self.parse_comment,
                                 headers={'Accept': 'application/json, text/javascript, */*; q=0.01',
                                          'Origin': 'https://vtv.vn',
                                          'Sec-Fetch-Mode': 'cors',
                                          'Referer': response.url},
                                 meta={'article': article})

    def parse_comment(self, response):
        str1 = ''
        log = response.meta['article']
        for text in response.xpath('//text()').getall():
            str1 += text
        try:
            list_inter = json.loads(str1)
            dict_inter = dict(list_inter[0])
            del dict_inter['url']
            log.update(dict_inter)
            self.logger.info("#%d: Scraping %s", self.articleCount,
                         log.get('link'))
            self.articleCount += 1
            yield log
        except:
            self.logger.info("#%d: Scraping %s", self.articleCount,
                             log.get('link'))
            self.articleCount += 1
            yield log

