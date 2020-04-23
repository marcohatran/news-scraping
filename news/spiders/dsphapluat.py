import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import json
import modules.timeConverter as time

class DoiSongPhapLuatSpider(CrawlSpider):
    name = "dspl"
    custom_settings = {
        'CONCURRENT_REQUESTS': 100,
        'REACTOR_THREADPOOL_MAXSIZE': 20,
        'LOG_LEVEL': 'INFO',
        'COOKIES_ENABLED': False,
        'RETRY_ENABLED': False,
        'REDIRECT_ENABLED': False,
        'AJAXCRAWL_ENABLED': True,
    }

    allowed_domains = ['www.doisongphapluat.com', 'sharefb.cnnd.vn', 'www.facebook.com']
    start_urls = ['https://www.doisongphapluat.com/']
    rules = (
        Rule(LinkExtractor(allow_domains=['www.doisongphapluat.com']), callback='parse_item', follow=True),
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
        title = response.xpath('//h1[@class="art-title"]/text()').extract_first()
        if title is not None:
            # get ld_json
            article= dict()
            ld_json = response.xpath('//script[contains(text(),"NewsArticle")]/text()').get()
            if ld_json is not None:
                try:
                    r = ld_json[::-1].replace(',', ' ', 1)[::-1]
                    article = json.loads(r)
                except ValueError:
                    article = dict()
            if 'dateModified' in article.keys():
                article.update({'dateModified': time.Dspl_timestamp(article.get('dateModified'))})
            if 'datePublished' in article.keys():
                article.update({'datePublished': time.Dspl_timestamp(article.get('datePublished'))})


            link = response.url
            article.update({'title': title, 'link': link})
            # get image
            thumbnail = response.xpath('(//td[@class="pic"]/div/img/@src)|(//td[@class="pic"]/h2/img/@src)|(//td['
                                       '@class="pic"]//img/@src)|(//div[@id="main-detail"]/div/a/img)|(//div['
                                       '@type="Photo"]/p/a/img/@src)').getall()
            article.update({'thumbnail': thumbnail})
            # get meta
            article.update({'type': response.xpath("//head/meta[@property='og:type']/@content").get()})
            article.update({'description': response.xpath("//meta[@name='description']/@content").get()})
            article.update({'keywords': response.xpath("//meta[@name='keywords']/@content").get()})
            article.update({'category': response.xpath("//meta[@property='article:section']/@content").get()})
            article.update({'copyright': response.xpath("//div[@class='listhome left'][2]/a/span/text()").get()})
            article.update({'language': response.xpath("//meta[@name='language']/@content").get()})
            article.update({'geo_place_name': response.xpath("//meta[@name = 'geo.placename']/@content").get()})
            article.update({'geo_region': response.xpath("//meta[@name = 'geo.region']/@content").get()})
            article.update({'geo_position': response.xpath("//meta[@name = 'geo.position']/@content").get()})
            article.update({'organization': 'Đời sống pháp luật'})
            # author
            content = ''
            for text in response.xpath(
                    '(//div[@id="main-detail"]/p[@style="text-align: justify;"]/text())|(//div['
                    '@id="main-detail"]/div[@style="text-align: justify;"]/p[@style="text-align: justify;"]/text())|('
                    '//div[@id="main-detail"]/div[@style="text-align: justify;"]/p[@style="text-align: '
                    'justify;"]/strong/text())|(//span[@style="font-size: small;"]/strong/em/text())|(//div['
                    '@id="main-detail"]/div[@style="text-align: justify;"]/p[@style="text-align: '
                    'justify;"]/div/h4/text())|(//em/text())').getall():
                content += text.strip()
            article.update({'content_article': content})
            if content is not None:
                word_count = len(content.split())
                article.update({'word_count': word_count})
            else:
                word_count = -1
                article.update({'word_count': word_count})
            # get related_urls
            relate_url = []
            htags = response.xpath('//ul[@class="listing pkg"]/li/h3[@class="title"]')
            for tag in htags:
                relate_urls = {}
                headline = tag.xpath('a/text()').get()
                url = str(tag.xpath('a/@href').extract_first())
                relate_urls.update({'headline': headline, 'url': url})
                relate_url.append(relate_urls)
            article.update({"related_url": relate_url})
            # get interactions
            id_article = dict()
            url = response.xpath('//meta[@property="og:url"]/@content').get()
            if url is not None:
                id_article.update({'url': url})
                like_request = "https://www.facebook.com/plugins/like.php?app_id=1547540628876392&channel=https%3A%2F" \
                               "%2Fstaticxx.facebook.com%2Fconnect%2Fxd_arbiter.php%3Fversiondomainvnexpress.net" \
                               "%26origin%3Dhttps%253A%252F%252Fvnexpress.netrelation%3Dparent.parent&container_width" \
                               "=0&href=" + \
                               id_article[
                                   'url'] + "&layout=button_count&locale=en_US&sdk=joey&send=false&show_faces=true&width=450"
                yield scrapy.Request(like_request, callback=self.parse_like, meta={'data': article, 'id_article': id_article})

            else:
                yield article

    def parse_share(self, response):
        log = response.meta['data']
        share = response.xpath('(//span[@id="u_0_3"]/text())|(//*[@id="u_0_4"]/text())').get()
        if share is not None:
            if "k" in share.lower():
                share = share.lower()
                share = share.replace(",", ".")
                share = share.replace("k", "")
                share = float(share) * 1000
            share = int(share)
        else:
            share = -1
        log.update({'share_count': share})
        self.logger.info("#%d: Scraping %s", self.articleCount,
                         log.get('link'))
        self.articleCount += 1
        yield log

    def parse_like(self, response):
        log = response.meta['data']
        id_article = response.meta['id_article']
        likes = response.xpath('(//span[@id="u_0_3"]/text())|(//*[@id="u_0_4"]/text())').get()
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
        share_rq = "https://www.facebook.com/plugins/share_button.php?app_id=197055007120496&channel" \
                                  "=https%3A%2F%2Fstaticxx.facebook.com%2Fconnect%2Fxd_arbiter.php" \
                                  "%3Fversiondomainvnexpress.net%26origin%3Dhttps%253A%252F%252Fvnexpress.netrelation" \
                                  "%3Dparent.parent&container_width=0&href=" + \
                                  id_article[
                                      'url'] + "&layout=button_count&locale=en_US&sdk=joey&send=false&show_faces=true" \
                                               "&width=450 "
        yield scrapy.Request(share_rq, callback=self.parse_share, meta={'data': log})

