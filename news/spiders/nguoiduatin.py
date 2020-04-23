# -*- coding: utf-8 -*-
import scrapy
import json

import modules.timeConverter as time


def remove_ctrl(string):
    string = string.replace('\n', '')
    string = string.replace('\0', '')
    string = string.replace('\t', '')
    string = string.replace('\r', '')
    return string


class NguoiDuatinSpider(scrapy.Spider):
    name = 'nguoiduatin'
    allowed_domains = ['nguoiduatin.vn']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.articleCount = 0

    def start_requests(self):
        return [scrapy.Request("https://www.nguoiduatin.vn/", callback=self.logged_in)]
        # return [scrapy.Request("https://www.nguoiduatin.vn/tap-chi-my-conde-nast-traveler-vinh-danh-intercontinental-danang-sun-peninsula-resort-la-khu-nghi-duong-tot-nhat-chau-a-a452528.html", callback=self.parse_article)]
        # return [scrapy.Request("https://www.nguoiduatin.vn/hau-due-mat-troi-viet-nam-tap-33-34-dai-uy-duy-kien-coi-quan-ham-di-cuu-nguoi-yeu-a409674.html", callback=self.parse_article)]

    def logged_in(self, response):
        urls = [
            "https://www.nguoiduatin.vn/c/video",
            "https://www.nguoiduatin.vn/c/chinh-tri-xa-hoi",
            "https://www.nguoiduatin.vn/c/phap-luat",
            "https://www.nguoiduatin.vn/c/the-gioi",
            "https://www.nguoiduatin.vn/c/da-chieu",
            "https://www.nguoiduatin.vn/c/giai-tri",
            "https://www.nguoiduatin.vn/c/kinh-doanh",
            "https://www.nguoiduatin.vn/c/doi-song",
            "https://www.nguoiduatin.vn/c/cong-nghe",
            "https://www.nguoiduatin.vn/c/can-biet",
            "https://www.nguoiduatin.vn/c/infocus"
        ]
        for url in urls:
            yield scrapy.Request(url)

    def parse(self, response):
        for href in response.xpath('/html/body//section[@class = "col"]//article/a/@href'):
            try:
                yield response.follow(href, self.parse_article)
            except Exception:
                self.logger.error("ERROR: ", exc_info=True)
                continue

        next_page = response.xpath(
            '/html/body//li[@class = "page-item next"]/a/@href').get()
        if next_page is not None:
            yield response.follow(next_page, self.parse)

    def parse_article(self, response):
        article = {}

        try:
            # get ld_json
            ld_json = response.xpath(
                '//html/head/script[contains(text(),"NewsArticle")]/text()').get()
            ld_json = remove_ctrl(ld_json)
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
            'category': response.xpath('//li[@class = "f-rsb m-auto nav-item position-relative d-inline-block active"]/a/text()').get(),
            'organization': 'người đưa tin',
            'url': response.url,
            'related_urls':  response.xpath('//section[@class = "article-content clearfix"]/following-sibling::section[@class = "row"]//li[@class = "box-news row pb-3 clearfix py-3 border-bottom "]/a/@href').getall()
        }
        article.update(elems)

        # get content
        content = ''
        for text in response.xpath('/html/body//section[@class = "article-content clearfix"]/article//text()').getall():
            content += text.strip()
        for text in response.xpath('//div[@class = "box-center"]/p/text()').getall():
            content += text.strip()
        article.update({'content': content})

        word_count = len(content.split())
        article.update({'word_count': word_count})

        # get image url
        images = {}
        type1_index = 0
        for type1_index, src in enumerate(response.xpath('/html/body//section[@class = "article-content clearfix"]//figure[@class = "tplCaption image"]/img/@src').getall(), 1):
            images.update({'image' + str(type1_index): src})
        type2_index = type1_index + 1
        for type2_index, src in enumerate(response.xpath('//*[contains(@class,"image-full-width") or contains(@class,"box")]/img/@src').getall(), type2_index):
            images.update({'image' + str(type2_index): src})
        article.update({'image-urls': images})

        url = response.url
        url = url.replace('https://www.nguoiduatin.vn/', '')
        id = response.xpath('//@data-id').get()
        if id is None:
            pv1 = response.url.find('.html')
            pv2 = response.url.find('a', pv1-7) + 1
            id = response.url[pv2:pv1]

        # get video urls
        id_finder = response.xpath(
            '//script[contains(@src,"//embed.easyvideo.vn/play")]/@src').get()
        if id_finder is not None:
            easyvideo_id = id_finder.replace('//embed.easyvideo.vn/play', '')
            video_finder = "https://embed.easyvideo.vn/render/" + \
                easyvideo_id+"?targetId=MeCloudLoader_"+easyvideo_id
            yield scrapy.Request(video_finder, callback=self.parse_video, meta={'article': article, 'url': url, 'id': id})
        else:
            # get likes
            like_request = "https://www.facebook.com/v2.9/plugins/like.php?action=like&app_id=1069396303196363&channel=https%3A%2F%2Fstaticxx.facebook.com%2Fconnect%2Fxd_arbiter.php%3Fversion%3D44%23cb%3Df122fdd10517174%26domain%3Dwww.nguoiduatin.vn%26origin%3Dhttps%253A%252F%252Fwww.nguoiduatin.vn%252Ff3f7ea1e941e5e4%26relation%3Dparent.parent&container_width=410&href=https%3A%2F%2Fwww.nguoiduatin.vn%2F" + url + "&layout=button_count&locale=vi_VN&sdk=joey&share=true&size=small"
            yield scrapy.Request(like_request, callback=self.parse_likes, meta={'article': article, 'id': id})

    def parse_video(self, response):
        article = response.meta['article']
        url = response.meta['url']
        id = response.meta['id']

        string = ''
        for a in response.xpath('//text()').getall():
            string += a
        pv1 = string.find('720p')
        if pv1 < 0:
            pv1 = string.find('480p')
            if pv1 < 0:
                pv1 = string.find('360p')
        pv2 = pv1 + string[pv1:].find(':') + 1
        pv3 = pv2 + string[pv2:].find('?')
        video_url = string[pv2:pv3]
        article.update({'video-url': video_url})

        # get likes
        like_request = "https://www.facebook.com/v2.9/plugins/like.php?action=like&app_id=1069396303196363&channel=https%3A%2F%2Fstaticxx.facebook.com%2Fconnect%2Fxd_arbiter.php%3Fversion%3D44%23cb%3Df122fdd10517174%26domain%3Dwww.nguoiduatin.vn%26origin%3Dhttps%253A%252F%252Fwww.nguoiduatin.vn%252Ff3f7ea1e941e5e4%26relation%3Dparent.parent&container_width=410&href=https%3A%2F%2Fwww.nguoiduatin.vn%2F" + url + "&layout=button_count&locale=vi_VN&sdk=joey&share=true&size=small"
        yield scrapy.Request(like_request, callback=self.parse_likes, meta={'article': article, 'id': id})

    def parse_likes(self, response):
        article = response.meta['article']
        id = response.meta['id']

        likes = response.xpath(
            '//button[@type="submit"]/div/span[3]/text()').get()
        if likes is None:
            likes = '0'
        article.update({'likes-counter': likes})

        cmt_request = "https://www.nguoiduatin.vn/article/" + \
            id+"/comments?page=1&&sort=newest"
        yield scrapy.Request(cmt_request, callback=self.parse_comments, meta={'article': article})

    def parse_comments(self, response):
        article = response.meta['article']

        str = ''
        for a in response.xpath('//text()').getall():
            str += a

        if str is 'null':
            article.update({'comments-count': 0, 'comments': ''})
            # return self.upload_article(article)
            self.logger.info("#%d: Scraping %s", self.articleCount,
                             article.get('url'))
            self.articleCount += 1
            return article

        cmt_dict = []
        check = 0
        string = ''

        response_dict = json.loads(str)
        comments = response_dict.get('data').get('comments')
        users = response_dict.get('data').get('anonymousUsers')

        for comment in comments:
            comment['SenderFullName'] = users.get(
                comment.pop('anonymousUserId')).get('fullName')
            comment['CommentContent'] = comment.pop('content')
            comment['CreatedDate'] = comment.pop('createdTime')
            comment['Liked'] = comment.pop('likeCount')
            comment['Replies'] = comment.pop('replies')
            cmt_dict.append(comment)

        article.update({'comments': cmt_dict})

        # return self.upload_article(article)
        self.logger.info("#%d: Scraping %s", self.articleCount,
                         article.get('url'))
        self.articleCount += 1
        return article
