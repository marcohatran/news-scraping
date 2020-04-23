from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import scrapy
import json
import modules.timeConverter as time

class TuoitreSpider(CrawlSpider):

    name = "tuoitre"
    custom_settings = {
        'CONCURRENT_REQUESTS': 100,
        'REACTOR_THREADPOOL_MAXSIZE': 20,
        'LOG_LEVEL': 'INFO',
        'COOKIES_ENABLED': False,
        'RETRY_ENABLED': False,
        'REDIRECT_ENABLED': False,
        'AJAXCRAWL_ENABLED': True,
    }
    allowed_domains = ['tuoitre.vn']
    start_urls = ['https://tuoitre.vn/']

    rules = (
        Rule(LinkExtractor(allow_domains=['tuoitre.vn'], deny_domains=['vieclam.tuoitre.vn']), callback='parse_item', follow=True),
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
        date = dict()
        title = response.xpath('//head/meta[@property="og:title"]/@content').extract_first()
        if title is not None:

            date.update({'datePublished': response.xpath('//meta[@property="article:published_time"]/@content').get()})
            date.update({'dateModified': response.xpath('//meta[@property="article:modified_time"]/@content').get()})
            if date is not None:
                try:
                    date = time.timestamp_converter(date)
                    article.update(date)
                except:
                    pass

            link = response.url
            article.update({'title': title, 'link': link})
            # get meta
            article.update({'headline': response.xpath('//meta[@itemprop="headline"]/@content').get()})
            article.update({'type': response.xpath("//meta[@property='og:type']/@content").get()})
            article.update({'description': response.xpath("//meta[@name='description']/@content").get()})
            article.update({'keywords': response.xpath("//meta[@name='keywords']/@content").get()})
            article.update({'category': response.xpath("//meta[@property='article:section']/@content").get()})
            article.update({'copyright': response.xpath("//meta[@name='copyright']/@content").get()})
            article.update({'language': response.xpath("//meta[@name='Language']/@content").get()})
            article.update({'geo_place_name': response.xpath("//meta[@name = 'geo.placename']/@content").get()})
            article.update({'geo_region': response.xpath("//meta[@name = 'geo.region']/@content").get()})
            article.update({'geo_position': response.xpath("//meta[@name = 'geo.position']/@content").get()})
            article.update({'organization': 'Tuổi trẻ'})

            # author
            content = ''
            author = ''
            for text in response.xpath('(//div|//p)[contains(@class, "author") or contains(@class, "author_single") or contains(@class,"authorvideo") or contains(@class,"credit-text")]//text()').getall():
                author += text.strip()
            article.update({'author': author})
            for text in response.xpath('//div[contains(@id,"main-detail-body") or contains(@class,"sp-detail-content") or contains(@class,"fck")]/p//text()').getall():
                content += text.strip()
            article.update({'content_article': content})
            word_count = len(content.split())
            article.update({'word_count': word_count})
            # get thumbnail
            thumbnail = response.xpath('(//div[@type="Photo"]/div/a/img/@src)|(//div[@type="Photo"]/div/img/@src)|(//td/a/img/@src)').getall()
            article.update({'thumbnail': thumbnail})
            # get images
            images = []
            image = dict()
            image.update({'url': response.xpath('//meta[@property="og:image"]/@content').get()})
            image.update({'alt': response.xpath('//meta[@property="og:image:alt"]/@content').get()})
            image.update({'width': response.xpath('//meta[@property="og:image:width"]/@content').get()})
            image.update({'height': response.xpath('//meta[@property="og:image:height"]/@content').get()})
            images.append(image)
            article.update({'image': images})
            # get relate_url
            relate_url = []
            htags = response.xpath('//ul[@class="list-news"]/li/div[@class="name-title"]')
            for tag in htags:
                relate_urls = {}
                headline = tag.xpath('a/text()').get()
                url = "https://tuoitre.vn" + str(tag.xpath('a/@href').extract_first())
                relate_urls.update({'headline': headline, 'url': url})
                relate_url.append(relate_urls)
            article.update({"related_url": relate_url})
            # get inf cmt
            objectid = response.xpath(
                '//div[@id="tagandnetwork"]/div[@class="tagandtopicandbanner"]/section/@data-objectid').get()
            if objectid is None:
                return 0
            else:
                objectid = objectid
            datasort = response.xpath(
                '//div[@id="tagandnetwork"]/div[@class="tagandtopicandbanner"]/section/@data-sort').get()
            if datasort is None:
                return 0
            else:
                datasort = datasort

            pagesize = response.xpath(
                '//div[@id="tagandnetwork"]/div[@class="tagandtopicandbanner"]/section/@data-pagesize').get()
            if pagesize is None:
                return 0
            else:
                pagesize = pagesize
            objecttype = response.xpath(
                '//div[@id="tagandnetwork"]/div[@class="tagandtopicandbanner"]/section/@data-objecttype').get()
            if objecttype is None:
                return 0
            else:
                objecttype = objecttype
            id_article = dict()
            id_article.update({'objectid': objectid, 'datasort': datasort, 'pagesize': pagesize, 'objecttype': objecttype})
            # get total likes
            total_like = "https://s1.tuoitre.vn/count-object.htm?newsId=" + objectid

            yield scrapy.Request(total_like, callback=self.parse_like,
                                 headers={'Accept': '*/*',
                                          'Origin': 'https://tuoitre.vn',
                                          'Referer': response.url,
                                          'Sec-Fetch-Mode': 'cors',
                                          },
                                 meta={'article': article, 'id_article': id_article})

    def parse_like(self, response):
        log = response.meta['article']
        id_article = response.meta['id_article']
        log.update({'like_count': response.text})
        cmt_resquest = 'https://id.tuoitre.vn/api/getlist-comment.api?pageindex=1&pagesize=' + id_article[
            'pagesize'] + '&objId=' + id_article['objectid'] + '&objType=' + id_article['objecttype'] + '&sort=' + \
                       id_article['datasort']
        yield scrapy.Request(cmt_resquest, callback=self.parse_comment, meta={'data1': log})

    def parse_comment(self, response):
        str1 = ''
        for text in response.xpath('//text()').getall():
            str1 += text
        dict = json.loads(str1)
        article = response.meta['data1']
        article.update({'comment_article': dict})
        self.logger.info("#%d: Scraping %s", self.articleCount,
                         article.get('link'))
        self.articleCount += 1
        yield article
