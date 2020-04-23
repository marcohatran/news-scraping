import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import modules.timeConverter as time
class SaostarSpider(CrawlSpider):
    name = "saostar"
    allowed_domains = ['saostar.vn', 'sharefb.cnnd.vn', 'www.facebook.com']
    start_urls = ['http://saostar.vn/']
    rules = (
        Rule(LinkExtractor(allow_domains=['saostar.vn']), callback='parse_item', follow=True),
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
        title = response.xpath('//div[@class="head-article"]/h1/@data-title').get()
        if title is not None:
            # get meta
            article.update({'headline': response.xpath('//meta[@itemprop="headline"]/@content').get()})
            article.update({'datePublished': response.xpath('//time[@itemprop="datePublished"]/@datetime').get()})
            article.update({'dateModified': response.xpath('//time[@itemprop="dateModified"]/@datetime').get()})
            article.update({'publisher': response.xpath('//div[@itemprop="publisher"]/span/text()').get()})
            article.update({'type': response.xpath("//head/meta[@property='og:type']/@content").get()})
            article.update({'description': response.xpath("//head/meta[@name='description']/@content").get()})
            article.update({'keywords': response.xpath("//head/meta[@name='keywords']/@content").get()})
            article.update({'category': response.xpath("//head/meta[@property='article:section']/@content").get()})
            article.update({'copyright': response.xpath("//head/meta[@name='copyright']/@content").get()})
            article.update({'Language': response.xpath("//head/meta[@name='Language']/@content").get()})
            article.update({'geo_place_name': response.xpath("//meta[@name = 'geo.placename']/@content").get()})
            article.update({'geo_region': response.xpath("//meta[@name = 'geo.region']/@content").get()})
            article.update({'geo_position': response.xpath("//meta[@name = 'geo.position']/@content").get()})
            article.update({'organization': 'Saostar'})
            article = time.timestamp_converter(article)
            url_img = response.xpath('//meta[@property="og:image"]/@content').get()
            if url_img is not None:
                image.update({'url': response.xpath('//meta[@property="og:image"]/@content').get()})
                image.update({'alt': response.xpath('//meta[@property="og:image:alt"]/@content').get()})
                image.update({'width': response.xpath('//meta[@property="og:image:width"]/@content').get()})
                image.update({'height': response.xpath('//meta[@property="og:image:height"]/@content').get()})
                images.append(image)
                article.update({'image': images})
            # title, link, author, content
            link = response.url
            article.update({'title': title, 'link': link})
            article.update({'author': response.xpath("//span[@class='writer']/text()").get()})
            content = ''
            for text in response.xpath('(//div[@id="content_detail"]/p/text())|'
                                       '(//span['
                                       '@class="wp-caption-text"]/text())').getall():
                content += text.strip()
            article.update({'content_article': content})
            if content is not None:
                word_count = len(content.split())
                article.update({'word_count': word_count})
            else:
                word_count = -1
                article.update({'word_count': word_count})

            # get image
            thumbnail = response.xpath('(//p/a/img/@src)|(//strong/a/img/@src)|(//div/a/img/@src)').getall()
            if thumbnail is not []:
                article.update({'thumbnail': thumbnail})
            # get relate_url
            relate_url = []
            htags = response.xpath(
                '(//div[@class="content-block"]/div[@class="post mt15 js-post "]/h4[@class="post-title pl15 dis-inline-block"])|(//h3[@class="post-title mb10"])')
            for tag in htags:
                relate_urls = {}
                headline = tag.xpath('a/text()').get()
                if headline is not []:
                    url = str(tag.xpath('a/@href').extract_first())
                    relate_urls.update({'headline': headline, 'url': url})
                    relate_url.append(relate_urls)
                article.update({"related_url": relate_url})
            # get interactions

            url = response.xpath('//meta[@itemprop="url"]/@content').get()
            like_request = "https://www.facebook.com/v2.8/plugins/like.php?action=like&channel=https%3A%2F%2Fstaticxx" \
                           ".facebook.com%2Fconnect%2Fxd_arbiter.php%3Fversion%3D44%23cb%3Df37cc7337bc398%26domain" \
                           "%3Dsaostar.vn%26origin%3Dhttps%253A%252F%252Fsaostar.vn%252Ff3ecd646e17999%26relation" \
                           "%3Dparent.parent&container_width=0&href=" + url \
                           + "&layout=button_count&locale=vi_VN&sdk=joey&share=true&show_faces=false"
            yield scrapy.Request(like_request, callback=self.parse_like, meta={'data': article})
        else:
            pass

    def parse_like(self, response):
        log = response.meta['data']
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
        self.logger.info("#%d: Scraping %s", self.articleCount,
                         log.get('link'))
        self.articleCount += 1
        yield log

