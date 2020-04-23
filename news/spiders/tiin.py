from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import scrapy
import modules.timeConverter as time


class TiinSpider(CrawlSpider):
    name = "tiin"
    custom_settings = {
        'CONCURRENT_REQUESTS': 100,
        'REACTOR_THREADPOOL_MAXSIZE': 20,
        'LOG_LEVEL': 'INFO',
        'COOKIES_ENABLED': False,
        'RETRY_ENABLED': False,
        'REDIRECT_ENABLED': False,
        'AJAXCRAWL_ENABLED': True,
    }
    allowed_domains = ['tiin.vn', 'sharefb.cnnd.vn', 'www.facebook.com']
    start_urls = ['http://tiin.vn/default.html']

    rules = (
        Rule(LinkExtractor(allow_domains=['tiin.vn'], deny_domains=['diemthi.tiin.vn']), callback='parse_item', follow=True),
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
        # get title, link, published
        title = response.xpath('//div[@id="body-content"]/h1[@id="title-container"]/span/text()').extract_first()
        if title is not None:
            # get meta
            article.update({'publisher': response.xpath('//meta[@name="dc.publisher"]/@content').get()})
            article.update({'type': response.xpath("//meta[@property='og:type']/@content").get()})
            article.update({'description': response.xpath("//meta[@name='description']/@content").get()})
            article.update({'keywords': response.xpath("//meta[@name='keywords']/@content").get()})
            article.update({'copyright': response.xpath("//head/meta[@name='copyright']/@content").get()})
            article.update({'language': response.xpath("//meta[@name='language'][2]/@content").get()})
            article.update({'geo_place_name': response.xpath("//meta[@name = 'geo.placename']/@content").get()})
            article.update({'geo_region': response.xpath("//meta[@name = 'geo.region']/@content").get()})
            article.update({'geo_position': response.xpath("//meta[@name = 'geo.position']/@content").get()})
            article.update({'geo_region': response.xpath("//meta[@name = 'geo.region']/@content").get()})
            article.update({'organization': 'Tiin'})
            link = response.url
            article.update({'title': title, 'link': link})
            category = response.xpath('//p[@id="breadcrumb"]/a/text()').get()
            article.update({'category': category.strip()})
            # datePublished
            datePublished = response.xpath('//p[@id="time"]/text()').get()
            datePublished = datePublished.strip()
            datePublished = time.Tiin_timestamp(datePublished)
            article.update({'datePublished': datePublished})

            dateModified = response.xpath('//p[@id="time"]/text()').get()
            dateModified = dateModified.strip()
            dateModified = time.Tiin_timestamp(dateModified)
            article.update({'dateModified': dateModified})

            # author
            content = ''
            author = ''
            for text in response.xpath(
                    '(//p[@class="article-author"]/text())|(//p[@class="article-author"]/a/text())|(//span['
                    '@class="text-source"]/text())').getall():
                author += text.strip()
            article.update({'author': author})
            for text in response.xpath('//div[@id="body-content"]/p/text()').getall():
                content += text.strip()
            article.update({'content_article': content})
            word_count = len(content.split())
            article.update({'word_count': word_count})
            # get relate_url
            relate_url = []
            htags = response.xpath(
                '//div[@class="tiin-news-relate"]/div[@class="wrap-news-relate"]/div[@class="news-relate-item"]')
            for tag in htags:
                relate_urls = {}
                headline = tag.xpath('a/@title').get()
                url = str(tag.xpath('a/@href').extract_first())
                relate_urls.update({'headline': headline, 'url': url})
                relate_url.append(relate_urls)
            article.update({"related_url": relate_url})

            # get image
            image = response.xpath('(//*[@id="body-content"]/p/img/@src)|(//*[@id="body-content"]/div/img/@src)').getall()
            article.update({'thumbnail': image})
            # get interactions
            like_request = "https://www.facebook.com/plugins/like.php?href=" + article[
                'link'] + "&width&layout=button_count&action=like&show_faces=true&share=true&height=21"
            yield scrapy.Request(like_request, callback=self.parse_like, meta={'data': article})
        else:
            pass

    def parse_like(self, response):
        log = response.meta['data']
        likes = response.xpath('(//span[@id="u_0_2"]/text())|(//*[@id="u_0_3"]/text())').get()
        if likes is not None:
            if "k" in likes.lower():
                likes = likes.lower()
                likes = likes.replace(",", ".")
                likes = likes.replace("k", "")
                likes = float(likes) * 1000
            likes = int(likes)
        else:
            likes = -1
        log.update({'like_count': likes})
        self.logger.info("#%d: Scraping %s", self.articleCount,
                         log.get('link'))
        self.articleCount += 1
        yield log