# -*- coding: utf-8 -*-
import scrapy
import json
from scrapy_splash import SplashRequest


class KipalogSpider(scrapy.Spider):
    name = 'kipalog'
    # start_urls = ["https://viblo.asia/newest"]

    prefix = 'https://kipalog.com'
    script = """
        function main(splash, args)
            assert(splash:go(args.url))
            assert(splash:wait(0.5))
            return splash:html()
        end
    """

    def __init__(self):
        self.articleCount = 0

    def start_requests(self):
        return [scrapy.Request("https://kipalog.com/posts/Toi-da-tiet-kiem--5-moi-thang-voi-Heroku-nhu-the-nao", callback=self.parse_article)]

    def parse(self, response):
        for post in response.xpath('//div[@class = "post-feed-item"]'):
            tags = []
            for tag in post.xpath('.//div[@class="tags"]/a/@href').getall():
                tag = "https://viblo.asia" + tag
                tags.append(tag)
            post_url = "https://viblo.asia" + post.xpath('.//h3/a/@href').get()
            yield SplashRequest(post_url, callback=self.parse_article, endpoint='render.html', args={'lua_source': self.script}, meta={'hash-tags': tags})

        next_page = response.xpath('//li[@class = "page-item"]/a/@href').get()
        if (next_page):
            yield response.follow(next_page, self.parse)

    def parse_article(self, response):
        article = {}

        # get ld_json
        try:
            ld_json = response.xpath(
                "//script[contains(text(),'Article')]/text()").get()
            ld_json_dict = json.loads(ld_json)
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
            'meta-content-language': response.xpath('//meta[@name = "content-language"]/@content').get(),
            'meta-geo.placename': response.xpath('//meta[@name = "geo.placename"]/@content').get(),
            'meta-geo.position': response.xpath('//meta[@name = "geo.region"]/@content').get(),
            'meta-geo.region': response.xpath('//meta[@name = "geo.region"]/@content').get(),
            'meta-article:author': response.xpath("//meta[@property='article:author']/@content").get(),
            'meta-article:publisher': response.xpath("//meta[@property='article:publisher']/@content").get(),
            'url': response.url
        }
        article.update(elems)

        # get related posts
        related = response.xpath(
            '//div[@class = "suggest posts list"]/div[@class = "ui massive list feed-list"]')[1]
        if related is not None:
            related_urls = []
            for url in related.xpath('.//div[@class="header"]/a/@href').getall():
                url = "https://kipalog.com" + url
                related_urls.append(url)
            article.update({'related-urls': related_urls})

        # get hashtags
        tags = []
        for tag in response.xpath('//h1/div[@class = "tag"]/a/@href').getall():
            tag = "https://kipalog.com" + tag
            tags.append(tag)
        article.update({'hash-tags': tags})

        # get likes/ upvotes counts
        likes = response.xpath(
            '//div[@class = "hidden-meta"]/input[contains(@ng-init, "like_count")]/@ng-init').get()
        likes = likes.replace('like_count=', '')
        article.update({'likes-counter': likes})

        # get content
        content = ''
        for text in response.xpath('//section[@id = "content"]//p/text()').getall():
            content += text.strip()
        article.update({'content': content})

        # get image url
        images = {}
        for index, src in enumerate(response.xpath('//section[@id = "content"]//img/@src').getall(), 1):
            images.update({'image' + str(index): src})

        article.update({'image-urls': images})

        # get comments
        postId = response.xpath(
            '//div[@class = "hidden-meta"]/input[contains(@ng-init, "postId")]/@ng-init').get()
        postId = postId.replace('postId=', '')
        postId = postId.replace("'", '')
        comment_url = "https://kipalog.com/posts/" + postId + "/comments"
        yield scrapy.Request(comment_url, callback=self.parse_comments, meta={'article': article})

    def parse_comments(self, response):
        article = response.meta['article']

        str = ''
        for a in response.xpath('//text()').getall():
            str += a

        if str is 'null':
            article.update({'comments-count': 0, 'comments': ''})
            self.logger.info("#%d: Scraping %s", self.articleCount,
                             article.get('url'))
            self.articleCount += 1
            return article

        cmt_dict = []
        check = 0
        string = ''

        for a in str:
            if a is '{':
                check = 1
            if check is 1:
                string += a
            if a is '}':
                check = 0
                string += a
                try:
                    cmt_dict.append(json.loads(string))
                except:
                    pass
                string = ''

        # No reply function
        cmt_count = len(cmt_dict)
        for cmt in cmt_dict:
            cmt['SenderFullName'] = cmt.get('user').pop("name")
            cmt['CommentContent'] = cmt.pop('content')
            cmt['Liked'] = cmt.pop('like_count')
            cmt['SenderAvatar'] = self.prefix + \
                cmt.get('user').pop('avatar_url_path')
            cmt.pop('user')
        article.update({'comments-count': cmt_count, 'comments': cmt_dict})

        self.logger.info("#%d: Scraping %s", self.articleCount,
                         article.get('url'))
        self.articleCount += 1
        return article
