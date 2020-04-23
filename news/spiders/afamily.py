from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import scrapy
import json
import modules.timeConverter as time

class AfamilySpider(CrawlSpider):
    name = "afamily"
    custom_settings = {
        'CONCURRENT_REQUESTS': 100,
        'REACTOR_THREADPOOL_MAXSIZE': 20,
        'LOG_LEVEL': 'INFO',
        'COOKIES_ENABLED': False,
        'RETRY_ENABLED': False,
        'REDIRECT_ENABLED': False,
        'AJAXCRAWL_ENABLED': True,
    }
    allowed_domains = ['http://afamily.vn/', 'sharefb.cnnd.vn', ]
    start_urls = ['http://afamily.vn/dep.chn',]

    rules = (
        Rule(LinkExtractor(allow_domains=['afamily.vn']), callback='parse_item', follow=True),
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
        image = dict()
        images = []
        try:
            ld_json = response.xpath('//script[contains(text(),"NewsArticle")]/text()').get()
            if ld_json is None:
                return 0
            else:
                ld_json = ld_json
                ld_json = json.loads(ld_json)
                ld_json = time.timestamp_converter(ld_json)
            article.update(ld_json)
        except ValueError:
            return 0
        title = response.xpath('//meta[@property="og:title"]/@content').get()
        link = response.url
        article.update({'title': title, 'link': link})
        # get meta
        article.update({'type': response.xpath("//head/meta[@property='og:type']/@content").get()})
        article.update({'description': response.xpath("//head/meta[@name='description']/@content").get()})
        article.update({'keywords': response.xpath("//meta[@name='keywords']/@content").get()})
        article.update({'category': response.xpath("//meta[@property='article:section']/@content").get()})
        article.update({'copyright': response.xpath("//meta[@name='copyright']/@content").get()})
        article.update({'language': response.xpath("//meta[@name='Language']/@content").get()})
        article.update({'geo_place_name': response.xpath("//meta[@name = 'geo.placename']/@content").get()})
        article.update({'geo_region': response.xpath("//meta[@name = 'geo.region']/@content").get()})
        article.update({'geo_position': response.xpath("//meta[@name = 'geo.position']/@content").get()})
        article.update({'organization': 'Afamily'})
        # author, content, title
        content = ''
        title = response.xpath('//div[@class="w700 mr-40 fl"]/h1/text()').getall()
        article.update({'title': title})
        for text in response.xpath(
                '(//div[@id="af-detail-content"]/p/text())|(//div[@data-role="content"]/div/span/text())|(//p['
                '@class="MsoNormal"]/text())|(//*[@id="af-detail-content"]/div/div/div/text())|(//*['
                '@id="af-detail-content"]/div/div/div/span/text())|(//*[@id="af-detail-content"]/div/div/p/text())').getall():
            content += text.strip()
        article.update({'content_article': content})
        if content is not None:
            word_count = len(content.split())
            article.update({'word_count': word_count})
        else:
            word_count = -1
            article.update({'word_count': word_count})
        url_image = response.xpath('//meta[@property="og:image"]/@content').get()
        if url_image is not None:
            image.update({'url': response.xpath('//meta[@property="og:image"]/@content').get()})
            image.update({'alt': response.xpath('//meta[@property="og:image:alt"]/@content').get()})
            image.update({'width': response.xpath('//meta[@property="og:image:width"]/@content').get()})
            image.update({'height': response.xpath('//meta[@property="og:image:height"]/@content').get()})
            images.append(image)
            article.update({'image': images})

        # get thumbnail
        thumbnail = response.xpath('(//div[@class="VCSortableInPreviewMode LayoutAlbumWrapper alignJustify noCaption"]/div/div/div/figure/a/@href)|(//div[@type="Photo"]/div/a/img/@src)|(//figure[@type="Photo"]/div/a/img/@src)|(//a[@class="detail-img-lightbox"]/img/@src)').getall()
        article.update({'thumbnail': thumbnail})
        with open("body.html","wb") as f:
            f.write(response.body)

        # get likes,comments
        yield scrapy.Request('http://sharefb.cnnd.vn/?urls=' + response.url, callback=self.parse_interations,
                             headers={'Accept': 'application/json, text/javascript, */*; q=0.01',
                                      'Origin': 'https://afamily.vn',
                                      'Sec-Fetch-Mode': 'cors',
                                      'Referer': article.get('link')},
                             meta={'article': article})

    def parse_interations(self, response):
        dict1 = {}
        str1 = response.xpath('//text()').get()
        article = response.meta['article']
        list_inter = json.loads(str1)
        dict_inter = dict(list_inter[0])
        del dict_inter['url']
        article.update(dict_inter)
        self.logger.info("#%d: Scraping %s", self.articleCount,
                         article.get('link'))
        self.articleCount += 1
        yield article