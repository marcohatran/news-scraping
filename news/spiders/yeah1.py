from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import json
import modules.timeConverter as time
class Yeah1Spider(CrawlSpider):
    name = "yeah1"
    allowed_domains = ['yeah1.com', 'sharefb.cnnd.vn',]
    start_urls = ['https://yeah1.com/']
    rules = (
        Rule(LinkExtractor(allow_domains=['yeah1.com']), callback='parse_item', follow=True),
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
        title = response.xpath('//meta[@property="og:title"]/@content').extract_first()
        if title is not None:
            # get ld json
            try:
                ld_json = response.xpath('//script[contains(text(),"NewsArticle")]/text()').get()
                if ld_json is None:
                    return 0
                else:
                    ld_json = ld_json
                article = json.loads(ld_json)
            except ValueError:
                return 0
            # get title, link

            if article is not None:
                article = article
            else:
                article = dict()

            datePublished = article.get('datePublished')
            if datePublished is not '':
                datePublished = time.Yeah1_timestamp(datePublished)
                article.update({'datePublished': datePublished})
            else:
                datePublished = response.xpath('//span[@class="time"]/text()').get()
                datePublished = datePublished.strip()
                datePublished = time.Tiin_timestamp(datePublished)
                article.update({'datePublished': datePublished})

            dateModified = article.get('dateModified')
            if dateModified is not '':
                dateModified = time.Yeah1_timestamp(dateModified)
                article.update({'dateModified': dateModified})
            else:
                dateModified = response.xpath('//span[@class="time"]/text()').get()
                dateModified = dateModified.strip()
                dateModified = time.Tiin_timestamp(dateModified)
                article.update({'dateModified': dateModified})

            link = response.url
            article.update({'title': title, 'link': link})
            # get meta
            article.update({'type': response.xpath("//head/meta[@property='og:type']/@content").get()})
            article.update({'description': response.xpath("//meta[@name='description']/@content").get()})
            article.update({'keywords': response.xpath("(//meta[@name='keywords']/@content)|(//meta[@name='news_keywords']/@content)").get()})
            article.update({'category': response.xpath("//meta[@property='category']/@content").get()})
            article.update({'copyright': response.xpath("//meta[@name='copyright']/@content").get()})
            article.update({'language': response.xpath("//meta[@name='language']/@content").get()})
            article.update({'geo_place_name': response.xpath("//meta[@name = 'geo.placename']/@content").get()})
            article.update({'geo_region': response.xpath("//meta[@name = 'geo.region']/@content").get()})
            article.update({'geo_position': response.xpath("//meta[@name = 'geo.position']/@content").get()})
            author = response.xpath('(//div[@class="article-content"]/p/strong/span/text())|((//div[@class="article-content"]/p/strong)[last()]/text())|((//div[@class="article-content"]/p)[last()]/text())').get()
            if author is None:
                author = response.xpath('//div[@class="card-meta"]/span[2]/text()').get()
            article.update({'author': author})
            article.update({'organization': 'Yeah1'})
            # author
            content = ''
            for text in response.xpath(
                '(//div[@class="article-content"]/p/text())|(//div[@class="article-content"]/h3/text())|(//p['
                '@class="card-text full-height"]/text())').getall():
                content += text.strip()
            article.update({'content_article': content})
            if content is not None:
                word_count = len(content.split())
                article.update({'word_count': word_count})
            else:
                word_count = -1
                article.update({'word_count': word_count})
            with open("body2.html", "wb") as f:
                f.write(response.body)
            # get image
            thumbnail = response.xpath('(//div[@class="article-content"]/p/a/img/@src)|(//figure/img/@src)').getall()
            if thumbnail is not None:
                article.update({'thumbnail': thumbnail})
            else:
                article.update({'thumbnail': '-1'})
            # get relate_url
            relate_url = []
            htags = response.xpath(
                '//div[@class="col-md-4"]/div[@class="card"]/div[@class="card-body"]/h4[@class="card-title"]')
            for tag in htags:
                relate_urls = {}
                headline = tag.xpath('a/@title').extract_first()
                if headline is not []:
                    url = str(tag.xpath('a/@href').extract_first())
                    relate_urls.update({'headline': headline, 'url': url})
                    relate_url.append(relate_urls)
                article.update({"related_url": relate_url})
            self.logger.info("#%d: Scraping %s", self.articleCount,
                            article.get('link'))
            self.articleCount += 1
            yield article
