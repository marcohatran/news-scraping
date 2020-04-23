import scrapy
import json
import modules.timeConverter as time

class VnexpressSpider(scrapy.Spider):
    name = 'vnexpress'
    start_urls = ['https://vnexpress.net/kinh-doanh']

    def __init__(self, crawlMode='', **kwargs):
        super().__init__(**kwargs)
        self.crawlMode = crawlMode
        if crawlMode is 'update' or crawlMode is '':
            self.crawlMode = 'Update'
        print(self.crawlMode)

        self.articleCount = 0

    def parse(self, response):
        menu = response.xpath('//body/nav[@id="main_menu"]/a/@href').getall()
        for link in menu:
            yield scrapy.Request(link, callback=self.parse_start)

    def parse_start(self, response):
        alllink = response.xpath('//article[@class="list_news"]/h4[@class="title_news"]/a[1]/@href').getall()
        for link in alllink:
            full_url = response.urljoin(link)
            yield scrapy.Request(full_url, callback=self.parse_article)
            next_page = response.xpath('//*[@id="pagination"]/a[@class="next"]/@href').get()
            if next_page is not None:
                next_page = response.urljoin(next_page)
                yield scrapy.Request(next_page, callback=self.parse_start)

    def parse_article(self, response):
        article = dict()
        title = response.xpath('(//h1[@class="title_news_detail mb10"]/text())|(//h1[@class="title"]/text())').get()
        if title is not None:
            # get ld_json
            try:
                ld_json = response.xpath('//script[contains(text(),"NewsArticle")]/text()').get()
                ld_json = json.loads(ld_json)
                ld_json = time.timestamp_converter(ld_json)
                article.update(ld_json)
            except:
                pass
            if 'datePublished' not in article.keys():
                datePublished = response.xpath('(//meta[@name="pubdate"]/@content)').get()
                if datePublished is not None:
                    datePublished = datePublished.strip()
                    datePublished = time.Vnex_timestamp(datePublished)
                    article.update({'datePublished': datePublished})
                else:
                    datePublished = response.xpath('//meta[@name="its_publication"]/@content').get()
                    article.update({'datePublished': datePublished})
            if 'dateModified' not in article.keys():
                dateModified = response.xpath('(//meta[@itemprop="dateModified"]/@content)').get()
                if dateModified is not None:
                    dateModified = dateModified.strip()
                    dateModified = time.Vnex_timestamp(dateModified)
                    article.update({'dateModified': dateModified})
                else:
                    dateModified = response.xpath('//meta[@name="article_updatetime"]/@content').get()
                    article.update({'dateModified': dateModified})
            link = response.url
            article.update({'link': link, 'title': title})
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
            article.update({'category': response.xpath("(//li[@class='start']/h4/a/text())|(//li[@class='start have_cap2 ']/h4/a/text())").get()})
            article.update({'organization': 'Vnexpress'})
            content = ''
            author = ''
            for text in response.xpath('(//section[@class="container"]/section[@class="wrap_sidebar_12"]/section['
                                   '@class="sidebar_1"]/article[@class="content_detail fck_detail width_common '
                                   'block_ads_connect"]/p[@class="Normal"]/strong/text())|(//p['
                                   '@class="author_mail"]/strong/text())|(//p['
                                   '@style="text-align:right;"]/strong/text())').getall():
                author += text.strip()
            article.update({'author': author})
            for text in response.xpath('(//article[@class="content_detail fck_detail width_common '
                                       'block_ads_connect"]/p/text())|(//div[@class="desc_cation"]/p/text())|(//div['
                                       '@class="desc_cation"]/p/strong/text())|(//div[contains(@class,'
                                       '"box_tableinsert") or contains(@class,"box_quangcao") or contains(@class,'
                                       '"box_brief_info")]//p//text())|(//div[@class="WordSection1"]/p/text())|(//td/p[@class="Image"]/text())').getall():
                content += text.strip()
            article.update({'content_article': content})
            if content is not None:
                word_count = len(content.split())
                article.update({'word_count': word_count})
            else:
                word_count = -1
                article.update({'word_count': word_count})
            # get image
            thumbnail = response.xpath('(//td/img/@src)|(//div[@class="item_slide_show clearfix"]/div/img/@src)').getall()
            if thumbnail is not None:
                article.update({'thumbnail': thumbnail})
            else:
                article.update({'thumbnail': '-1'})
            # get relate_url
            relate_urls = []
            htags = response.xpath('//ul[@class="list_title"]/li/a[@data-event-action="article_box_related"]')
            for tag in htags:
                relate_url = dict()
                headline = tag.xpath('/@title').get()
                url = "https://vnexpress.vn" + str(tag.xpath('/@href').extract_first())
                relate_url.update({'headline': headline, 'url': url})
                relate_urls.append(relate_url)
            article.update({"related_url": relate_urls})
            # get comment
            id_article = dict()
            objectid = response.xpath('//head/meta[@name="tt_article_id"]/@content').get()
            if objectid is None:
                return 0
            else:
                objectid = objectid
            siteid = response.xpath('//head/meta[@name="tt_site_id"]/@content').get()
            if siteid is None:
                return 0
            else:
                siteid = siteid
            categoryid = response.xpath('//head/meta[@name="tt_category_id"]/@content').get()
            if categoryid is None:
                return 0
            else:
                categoryid = categoryid

            id_article.update({'objectid': objectid, 'siteid': siteid, 'categoryid': categoryid})
            url_like = response.xpath('//meta[@name="its_url"]/@content').get()
            if url_like is not None:
                # get total like
                like_request = "https://www.facebook.com/plugins/like.php?href=" + url_like + "&layout=button_count"
                yield scrapy.Request(like_request, callback=self.parse_like, meta={'article': article, 'id_article': id_article})
            else:
                pass
        # get comment

    def parse_comment(self, response):
        str1 = ''
        dict_cmt = dict()
        for text in response.xpath('//text()').getall():
            str1 += text
        if str1 is not None:
            try:
                dict_cmt = json.loads(str1)
            except ValueError:
                dict_cmt.update({'data': 'None'})
            data_all = dict_cmt["data"]
            if "items" in data_all:
                dict_cmt["data_vn"] = data_all["items"]
                del dict_cmt["data"]
                log = response.meta['data']
                log.update({'comment_article': dict_cmt})
            else:
                log = response.meta['data']
                log.update({'comment_article': dict_cmt})
        else:
            dict_cmt = json.loads(str1)
            log = response.meta['data']
            log.update({'comment_article': dict_cmt})
        self.logger.info("#%d: Scraping %s", self.articleCount,
                        log.get('link'))
        self.articleCount += 1
        yield log

    def parse_like(self, response):
        log = response.meta['article']
        id_article = response.meta['id_article']
        likes = response.xpath('(//span[@id="u_0_3"]/text())|(//*[@id="u_0_4"]/text())|(//span[@id="u_0_2"]/text())').get()
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
        cmt_resquest = 'https://usi-saas.vnexpress.net/index/get?offset=0&limit=24&frommobile=0&sort=like&is_onload=1' \
                       '&objectid=' + id_article['objectid'] + '&objecttype=1&siteid='+ id_article['siteid'] + \
                       '&categoryid=' + id_article['categoryid']
        yield scrapy.Request(cmt_resquest, callback=self.parse_comment, meta={'data': log})
