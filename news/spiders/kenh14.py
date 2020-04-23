import scrapy
import json
import ast

import modules.timeConverter as time


class Kenh14Spider(scrapy.Spider):
    name = 'kenh14'
    allowed_domains = ['kenh14.vn']

    def __init__(self, crawlMode='', **kwargs):
        super().__init__(**kwargs)
        self.crawlMode = crawlMode
        if crawlMode is 'update' or crawlMode is '':
            self.crawlMode = 'Update'

        self.articleCount = 0

    def start_requests(self):
            # return [scrapy.Request("http://kenh14.vn/co-moi-chuyen-mua-meo-o-dau-cung-gay-bao-mxh-ua-met-khong-met-thi-coi-cam-nang-de-hoi-phat-an-luon-ne-20191021231634269.chn", callback=self.parse_article)]
            # return [scrapy.Request("http://kenh14.vn/star.chn", callback=self.parse_nav)]
        return [scrapy.Request("http://kenh14.vn/", callback=self.logged_in)]

    def logged_in(self, response):
        urls = [
            'http://kenh14.vn/star.chn',
            'http://kenh14.vn/tv-show.chn',
            'http://kenh14.vn/cine.chn',
            'http://kenh14.vn/musik.chn',
            'http://kenh14.vn/beauty-fashion.chn',
            'http://kenh14.vn/doi-song.chn',
            'http://kenh14.vn/an-quay-di.chn',
            'http://kenh14.vn/xa-hoi.chn',
            'http://kenh14.vn/the-gioi.chn',
            'http://kenh14.vn/sport.chn',
            'http://kenh14.vn/hoc-duong.chn',
            'http://kenh14.vn/hoc-duong.chn',
            'http://kenh14.vn/suc-khoe-gioi-tinh.chn',
            'http://kenh14.vn/2-tek.chn'
        ]
        for url in urls:
            yield scrapy.Request(url, callback=self.parse_nav)

    def parse_nav(self, response):
        # get category ID
        cate_id_finder = response.xpath(
            '//script[contains(text(),"CateId")]/text()').get()
        pv1 = cate_id_finder.find('CateId')
        pv2 = cate_id_finder.find("'", pv1)+1
        pv3 = cate_id_finder.find("'", pv2)
        cate_id = cate_id_finder[pv2:pv3]
        # call timeline request
        timeline_request = "http://kenh14.vn/timeline/laytinmoitronglist-1-0-0-0-0-0-" + \
            cate_id+"-0-0-0-0.chn"
        return scrapy.Request(timeline_request, callback=self.parse, meta={'page_index': 2, 'cate_id': cate_id})

    def parse(self, response):
        page_index = response.meta['page_index']
        cate_id = response.meta['cate_id']
        if response.xpath('//li[@class="knswli need-get-value-facebook clearfix "]//h3[@class="knswli-title"]/a/@href').get() is None:
            return
        for href in response.xpath('//li[@class="knswli need-get-value-facebook clearfix "]//h3[@class="knswli-title"]/a/@href'):
            try:
                yield response.follow(href, self.parse_article)
            except Exception:
                self.logger.error("ERROR: ", exc_info=True)
                continue
        # call timeline request
        timeline_request = "http://kenh14.vn/timeline/laytinmoitronglist-"+str(page_index)+"-0-0-0-0-0-" + \
            cate_id+"-0-0-0-0.chn"
        yield scrapy.Request(timeline_request, callback=self.parse, meta={'page_index': page_index+1, 'cate_id': cate_id})

    def parse_article(self, response):
        article = {}

        try:
            ld_json = response.xpath(
                "//script[contains(text(),'NewsArticle')]/text()").get()
            ld_json_dict = json.loads(ld_json)
            ld_json_dict = time.timestamp_converter(ld_json_dict)
            article.update(ld_json_dict)
        except:
            pass

        # get meta
        elems = {
            'meta-description': response.xpath("//meta[@name='description']/@content").get(),
            'meta-keywords': response.xpath("//meta[@name='keywords']/@content").get(),
            'meta-title': response.xpath("//meta[@name='title']/@content").get(),
            'meta-copyright': response.xpath("//meta[@name='copyright']/@content").get(),
            'meta-author': response.xpath("//meta[@name='author']/@content").get(),
            'language': response.xpath('//meta[@http-equiv = "content-language"]/@content').get(),
            'geo.placename': response.xpath('//meta[@name = "geo.placename"]/@content').get(),
            'geo.position': response.xpath('//meta[@name = "geo.region"]/@content').get(),
            'geo.region': response.xpath('//meta[@name = "geo.region"]/@content').get(),
            'meta-article:author': response.xpath("//meta[@property='article:author']/@content").get(),
            'meta-article:publisher': response.xpath("//meta[@property='article:publisher']/@content").get(),
            'category': response.xpath('//li[@class = "kmli active"]/a/text()').get(),
            'organization': 'kênh 14',
            'related_urls': response.xpath('//div[@class = "kds-same-category clearfix"]//div[@class = "rowccm"]/li/a/@href').getall(),
            'url': response.url
        }
        article.update(elems)

        # get content
        content = ''
        for text in response.xpath('//div[@class = "knc-content"]//p//text()').getall():
            content += text.strip()
        article.update({'content': content})

        word_count = len(content.split())
        article.update({'word_count': word_count})

        # get image url
        images = {}
        for index, src in enumerate(response.xpath('//div[@class = "knc-content"]//div[@type = "Photo"]//@src').getall(), 1):
            images.update({'image' + str(index): src})
        article.update({'image-urls': images})

        # get video url
        videos = {}
        for index, src in enumerate(response.xpath('//div[@type="VideoStream"]/@data-src').getall(), 1):
            videos.update({'video'+str(index): src})
        article.update({'video-urls': videos})

        # get hashtags
        hashtags = {}
        for index, href in enumerate(response.xpath('//ul[@class="knt-list"]/li//@href').getall(), 1):
            hashtags.update({'tag'+str(index): href})
        article.update({'hash-tags': hashtags})

        comments_paras = response.xpath(
            '//script[@type="text/javascript"][contains(text(),"comment")]/text()').get()
        pv0 = comments_paras.find("MINGID_IFRAME_FUNC.mingidGenIfram")
        pv1 = comments_paras.find("(", pv0)
        pv2 = comments_paras.find(")", pv1)+1
        paras = comments_paras[pv1:pv2]
        # danh sach parameters de lay request comment
        para_list = ast.literal_eval(paras)
        para_list = list(para_list)

        # get interactions
        inter_request = "https://sharefb.cnnd.vn/?urls=" + response.url
        yield scrapy.Request(inter_request, callback=self.get_inter, meta={'article': article, 'paras': para_list}, headers={
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Origin': 'https://soha.vn',
            'Referer': 'https://soha.vn/chiu-suc-ep-khong-lo-tu-my-tq-ngam-ngui-buong-tay-bo-roi-du-an-dau-mo-5-ti-usd-voi-doi-tac-lau-nam-20191007161429421.htm',
            'Sec-Fetch-Mode': 'cors',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36'
        })

    # get interactions
    def get_inter(self, response):
        article = response.meta['article']
        paras = response.meta['paras']

        inter = response.xpath('//text()').get()
        inter_dict = json.loads(inter)[0]
        del inter_dict['url']

        article.update(inter_dict)

        content_url = paras[3]
        news_title = paras[4]

        comment_request = "https://comment.vietid.net/comments?app_key=d9c694bd04eb35d96f1d71a84141d075&content_url=" + \
            content_url+"&news_title="+news_title
        yield scrapy.Request(comment_request, callback=self.parse_comment, meta={'article': article})

    # get comments
    def get_comment(self, response, XPATH, comments_counter):
        comments = []
        for comment in response.xpath(XPATH):
            comment_dict = {}
            primary_comment = comment.xpath('./div[contains(@id,"form")]')
            primary_ava = primary_comment.xpath(
                './/div[@class="avatar"]//img/@src').get()
            primary_user = primary_comment.xpath(
                './/a[@class="full-name"]/text()').get()
            if primary_user is not None:
                primary_user = primary_user.strip()
            primary_time = primary_comment.xpath(
                './/span[@class="time-ago"]/text()').get()
            if primary_time is not None:
                primary_time = primary_time.strip()
            primary_geo = primary_comment.xpath(
                './/span[@class="city"]/text()').get()
            if primary_geo is not None:
                primary_geo = primary_geo.strip()
            primary_content = primary_comment.xpath(
                './/div[@class="cm-content"]/span/text()').get()
            if primary_content is not None:
                primary_content = primary_content.strip()
            primary_likes = primary_comment.xpath(
                './/a[contains(@class,"vote-count")]/text()').get()
            if primary_likes is not None:
                primary_likes = primary_likes.strip()

            comment_dict.update({
                'SenderAvatar': primary_ava,
                'SenderFullName': primary_user,
                'CreatedDate': time.comment_time(primary_time),
                'PublishedGeo': primary_geo,
                'CommentContent': primary_content,
                'Liked': primary_likes,
            })
            comments_counter += 1
            if response.xpath('.//ul[@class="sub-cm "]') is None:
                comment_dict.update({'Replies-count': 0,
                                     'Replies': None})
                comments.append(comment_dict)
            else:
                [secondary_comments, secondary_count] = self.get_comment(
                    comment, './/ul[@class="sub-cm "]/li', 0)
                comment_dict.update({'Replies-count': secondary_count,
                                     'Replies': secondary_comments})
            comments.append(comment_dict)
        return [comments, comments_counter]

    def parse_comment(self, response):
        article = response.meta['article']
        comments = self.get_comment(
            response, '//ul[@class = "cm-list"]/li', 0)[0]
        article.update({'comments': comments})

        self.logger.info("#%d: Scraping %s", self.articleCount,
                         article.get('url'))
        self.articleCount += 1
        return article
