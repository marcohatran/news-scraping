# -*- coding: utf-8 -*-
import scrapy
import json

import modules.timeConverter as time


class VibloSpider(scrapy.Spider):
    name = 'viblo'
    prefix = "https://viblo.asia"

    def start_requests(self):
        # return [SplashRequest("https://viblo.asia/newest", callback=self.parse, endpoint='render.html')]
        return [scrapy.Request("https://viblo.asia/newest", callback=self.parse)]

    def __init__(self, crawlMode='', **kwargs):
        super().__init__(**kwargs)
        self.crawlMode = crawlMode
        if crawlMode is 'update' or crawlMode is '':
            self.crawlMode = 'Update'

        self.articleCount = 0

    def parse(self, response):
        for post in response.xpath('//div[@class = "post-feed-item"]'):
            try:
                tags = []
                for tag in post.xpath('.//div[@class="tags"]/a/@href').getall():
                    tag = self.prefix + tag
                    tags.append(tag)
                post_url = self.prefix + post.xpath('.//h3/a/@href').get()
                # yield SplashRequest(post_url, callback=self.parse_article, meta={'splash': {'endpoint': 'execute', 'args': {'lua_source': self.script}}, 'hash-tags': tags})
                yield scrapy.Request(post_url, callback=self.parse_article, meta={'hash-tags': tags})
            except Exception:
                self.logger.error("ERROR: ", exc_info=True)
                continue

        next_page = response.xpath(
            '//li[@class = "page-item"]/a[@rel = "next"]/@href').get()
        if next_page is not None:
            yield response.follow(next_page, callback=self.parse)

    def parse_article(self, response):
        article = {}

        # get ld_json
        try:
            ld_json = response.xpath(
                "//script[contains(text(),'Article')]/text()").get()
            if (ld_json is None):
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
            'meta-content-language': response.xpath('//meta[@name = "content-language"]/@content').get(),
            'meta-geo.placename': response.xpath('//meta[@name = "geo.placename"]/@content').get(),
            'meta-geo.position': response.xpath('//meta[@name = "geo.region"]/@content').get(),
            'meta-geo.region': response.xpath('//meta[@name = "geo.region"]/@content').get(),
            'meta-article:author': response.xpath("//meta[@property='article:author']/@content").get(),
            'meta-article:publisher': response.xpath("//meta[@property='article:publisher']/@content").get(),
            'url': response.url,
            'category': 'viblo article',
            'organization': 'viblo',
            'related-urls': response.xpath('//div[@class = "related-posts-box"]//div[contains(@class, "post-card__title")]//a/@href').getall()
        }
        article.update(elems)

        # get hashtags
        article.update({'hash-tags': response.meta['hash-tags']})

        # get views
        views = response.xpath(
            '//div[contains(@data-original-title, "Views:")]/@data-original-title').get()
        if views is not None:
            strings = [s for s in views.split() if s.isdigit()]
            if len(strings) != 0:
                views = strings[0]
            else:
                views = '0'
            article.update({'view-count': views})

        # get likes/ upvotes counts
        likes = response.xpath(
            '//div[@class = "votes votes--side post-actions__vote mb-1"]/div/text()').get()
        if likes is not None:
            likes = likes.replace('+', '')
            likes = likes.replace('\n', '')
            likes = likes.strip()
            article.update({'likes-counter': likes})

        # get comments count
        comment_count = response.xpath(
            '//div[@class = "post-meta__item mr-1"]//button[@class = "el-button el-button--text"]/span/text()').get()
        if comment_count is not None:
            comment_count = comment_count.replace('\n', '').strip()
            article.update({'comments-count': comment_count})
        else:
            article.update({'comments-count': '0'})

        # get content
        content = ''
        for text in response.xpath('//div[contains(@class, "md-contents article-content__body")]//text()').getall():
            content += text.strip()
        article.update({'content': content})

        word_count = len(content.split())
        article.update({'word_count': word_count})

        # get image url
        images = {}
        for index, src in enumerate(response.xpath('//div[contains(@class, "md-contents article-content__body")]//img/@src').getall(), 1):
            images.update({'image' + str(index): src})

        article.update({'image-urls': images})

        # get comments
        id = response.url.split('-')
        id = id[len(id) - 1]
        comment_url = "https://viblo.asia/api/posts/" + id + "/comments"
        return scrapy.Request(comment_url, callback=self.parse_comments, meta={'article': article})

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

        cmt_dict = json.loads(str)
        Comments = []

        for index, comment in enumerate(cmt_dict.get('comments').get('data'), 0):

            comment['SenderFullName'] = comment.get(
                'user').get('data').get('name')
            comment['CommentContent'] = comment.pop('contents')
            comment['CreatedDate'] = time.comment_time(
                comment.pop('created_at'))
            comment['Liked'] = comment.pop('points')
            comment['Replies'] = []

            if comment.get('in_reply_to_comment') is not None:
                for cmt in cmt_dict.get('comments').get('data'):
                    if cmt.get('id') is comment.get('in_reply_to_comment'):
                        cmt.get('Replies').append(comment)
                del cmt_dict.get('comments').get('data')[index]
            Comments.append(comment)

        article.update({'comments': Comments})

        self.logger.info("#%d: Scraping %s", self.articleCount,
                         article.get('url'))
        self.articleCount += 1
        return article
