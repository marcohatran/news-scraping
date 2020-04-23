import scrapy
import json

import modules.timeConverter as time


class ZingSpider(scrapy.Spider):
    name = 'zing'
    allowed_domains = ['news.zing.vn']

    def __init__(self, crawlMode='', **kwargs):
        super().__init__(**kwargs)
        self.crawlMode = crawlMode
        if crawlMode is 'update' or crawlMode is '':
            self.crawlMode = 'Update'

        self.articleCount = 0

    def start_requests(self):
        return [scrapy.Request("https://news.zing.vn/", callback=self.logged_in)]
       # return [scrapy.Request("https://news.zing.vn/chu-tich-tap-doan-hoa-binh-chung-toi-muon-nang-tam-du-lich-viet-post999148.html", callback=self.parse_article, meta={'viral': '20'})]
       # return [scrapy.Request("https://news.zing.vn/video-doan-van-hau-toi-met-nhung-luon-san-sang-cho-tuyen-viet-nam-post998925.html", callback=self.parse_video)]

    def logged_in(self, response):
        # scrape news
        for href in response.xpath('//*[@id="zing-header"]//div[@class = "subcate"]//li/a/@href'):
            yield response.follow(href)
        # scrape video
        video_href = response.xpath(
            '//*[@id="section-multimedia"]//*[text()="VIDEO"]/@href').get()
        yield response.follow(video_href, self.parse_video_nav)

    def parse(self, response):
        for article in response.xpath('//*[@id="news-latest"]/section/div//article'):
            viral_count = {
                'viral-count':  article.xpath('./descendant::span[@class = "viral-count "]/text()').get()
            }

            href = article.xpath('./descendant::a/@href').get()
            try:
                yield scrapy.Request("https://news.zing.vn"+href, self.parse_article, meta={
                    'viral': viral_count})
            except Exception:
                self.logger.error("ERROR: ", exc_info=True)
                continue

        next_page = response.xpath(
            '//*[@id="news-latest"]/section/div/p/a/@href').get()
        if next_page != None:
            yield response.follow(next_page, self.parse)

    def parse_article(self, response):
        article = {}

        # get ld_json
        try:
            ld_json = response.xpath(
                '//script[contains(text(),"NewsArticle")]/text()').get()
            ld_json_dict = json.loads(ld_json)
            ld_json_dict = time.timestamp_converter(ld_json_dict)
            article.update(ld_json_dict)
        except:
            pass

        # get meta elements
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
            'category': response.xpath('//p[@class = "the-article-category"]/a/text()').get(),
            'organization': 'zing',
            'related_urls': response.xpath('//div[@class = "article-list layout-grid-3"]//article/p/a/@href').getall(),
            'url': response.url
        }
        article.update(elems)
        article.update(response.meta['viral'])

        # get content
        content = ''
        for text in response.xpath('//*[@id="page-article"]/div[@class="page-wrapper"]/descendant::div[@class = "the-article-body"]/p/text()').getall():
            content += text.strip()
        article.update({'content': content})

        word_count = len(content.split())
        article.update({'word_count': word_count})

        # get image url
        images = {}
        for index, src in enumerate(response.xpath('//*[@id="page-article"]/div[@class="page-wrapper"]/descendant::table[@class = "picture"]//img/@src').getall(), 1):
            images.update({'image' + str(index): src})
        article.update({'image-urls': images})

        # get video url
        videos = {}
        for index, src in enumerate(response.xpath('//figure[@class="video cms-video"]/@data-video-src').getall(), 1):
            videos.update({'video' + str(index): src})
        article.update({'video urls': videos})

        # get comments
        id = response.xpath('//@article-id').get()
        cmt_request = "https://api.news.zing.vn/api/comment.aspx?action=get&id="+id
        yield scrapy.Request(cmt_request, callback=self.parse_comments, meta={'article': article})

    def parse_comments(self, response):
        article = response.meta['article']

        str = ''
        for a in response.xpath('//text()').getall():
            str += a

        dict = json.loads(str, strict=False)
        if len(dict) is not 0:
            dict.pop('current_page')
            comments_list = dict.get('comments')
            if comments_list is not None and len(comments_list) is not 0:
                for comment in comments_list:
                    comment['SenderFullName'] = comment.pop('DisplayName')
                    comment['CommentContent'] = comment.pop('Comment')
                    comment['CreatedDate'] = comment.pop('CreationDate')
                    comment['Liked'] = comment.pop('Like')
                    if comment['Replies'] is not None:
                        for reply in comment['Replies']:
                            reply['SenderFullName'] = reply.pop('DisplayName')
                            reply['CommentContent'] = reply.pop('Comment')
                            reply['CreatedDate'] = reply.pop('CreationDate')
                            reply['Liked'] = reply.pop('Like')
                            reply['Replies'] = []

        article.update(dict)
        self.logger.info("#%d: Scraping %s", self.articleCount,
                         article.get('url'))
        self.articleCount += 1
        return article

    def parse_video_nav(self, response):
        for video in response.xpath('//div[@class = "article-list listing-layout"]/article'):
            try:
                viral = video.xpath(
                    './header/p[@class = "article-meta"]//span[@class = "viral-count"]/text()').get()
                if viral is None:
                    viral = 'None'
                view = video.xpath(
                    './header/p[@class = "article-meta"]//span[@class = "view-count"]/text()').get()
                if view is None:
                    view = 'None'
                viral = {
                    'viral-count': viral,
                    'view-count': view
                }
                passing_url = "https://news.zing.vn" + \
                    video.xpath('./p/a/@href').get()
                yield scrapy.Request(passing_url, callback=self.parse_video, meta={'viral': viral})
            except Exception:
                self.logger.error("ERROR: ", exc_info=True)
                continue
        next_page = response.xpath(
            '// div[@class="article-list listing-layout"]/ul[@class = "pagination"]//@href')
        if next_page is not None:
            next_page = next_page[0]
            yield response.follow(next_page, self.parse_video_nav)

    def parse_video(self, response):
        video = {}

        # get ld+json
        ld_json = response.xpath(
            '//script[@type = "application/ld+json"]/text()').get()
        video = json.loads(ld_json, strict=False)

        # get elems
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
            'category': 'textArticle',
            'related_urls': response.xpath('//div[@class = "article-list layout-grid-3"]//article/p/a/@href').getall(),
            'url': response.url
        }
        video.update(elems)

        # get video source
        video.update({"video-source": response.xpath(
            '//div[@id = "video-featured"]//video/source[@res="720"]/@src').get()})

        # get viral info
        video.update(response.meta['viral'])

        # get comments
        id = response.xpath('//@article-id').get()
        cmt_request = "https://api.news.zing.vn/api/comment.aspx?action=get&id="+id
        yield scrapy.Request(cmt_request, callback=self.parse_comments, meta={'article': video})
