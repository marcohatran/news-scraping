from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import json
import modules.timeConverter as time


class BaoMoiSpider(CrawlSpider):
    name = "baomoi"
    #allowed_domains = ['baomoi.com', 'sharefb.cnnd.vn']
    allowed_domains = ['https://baomoi.com/', ]
    start_urls = ['https://baomoi.com/']

    rules = (
        Rule(LinkExtractor(allow_domains=['baomoi.com']), callback='parse_item', follow=True),
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
        # get title, link
        title = response.xpath('//div[@class="article"]/h1[@class="article__header"]/text()').extract_first()
        if title is not None:
            # get ld_json
            try:
                ld_json = response.xpath("//script[@type='application/ld+json'][1]/text()").get()
                ld_json = json.loads(ld_json)
                ld_json = time.timestamp_converter(ld_json)
                article.update(ld_json)
            except:
                pass
            # get meta
            article.update({'type': response.xpath("//head/meta[@property='og:type']/@content").get()})
            article.update({'description': response.xpath("//head/meta[@name='description']/@content").get()})
            article.update({'keywords': response.xpath("//head/meta[@name='keywords']/@content").get()})
            article.update({'category': response.xpath("//head/meta[@property='article:section']/@content").get()})
            article.update({'copyright': response.xpath("//head/meta[@name='copyright']/@content").get()})
            article.update({'Language': response.xpath("//head/meta[@name='Language']/@content").get()})
            article.update({'geo_place_name': response.xpath("//meta[@name = 'geo.placename']/@content").get()})
            article.update({'geo_region': response.xpath("//meta[@name = 'geo.region']/@content").get()})
            article.update({'geo_position': response.xpath("//meta[@name = 'geo.position']/@content").get()})
            article.update({'organization': 'Báo mới'})
            link = response.url
            article.update({'title': title, 'link': link})
            # author, content, word_count
            content = ''
            author = ''
            for text in response.xpath(
                    '(//div[@id="ArticleContent"]/p[@class="t-j"]/span/text())|(//div[@class="article__body"]/p['
                    '@class="body-text body-author"]/strong/text())|(//p[@class="body-text body-author"]/strong/text())').getall():
                author += text.strip()
            article.update({'author': author})
            for text in response.xpath(
                    '(//div[@id="ArticleContent"]/p[@class="t-j"]/text())|(//div[@class="article__body"]/p['
                    '@class="body-text"]/text())|(//div[@class="article__sapo"]/text())').getall():
                content += text.strip()
            article.update({'content_article': content})
            word_count = len(content.split())
            article.update({'word_count': word_count})
            # get image
            thumbnail = response.xpath('//p[@class="body-image"]/img/@src').getall()
            article.update({'thumbnail': thumbnail})
            # get related_url
            relate_url = []
            htags = response.xpath('//div[@data-track="detail|related"]/div/h4')
            for tag in htags:
                relate_urls = {}
                headline = tag.xpath('a/@title').get()
                url = str(tag.xpath('a/@href').extract_first())
                relate_urls.update({'headline': headline, 'url': url})
                relate_url.append(relate_urls)
            article.update({"related_url": relate_url})
            self.logger.info("#%d: Scraping %s", self.articleCount,
                             article.get('link'))
            self.articleCount += 1
            yield article
        else:
            pass
