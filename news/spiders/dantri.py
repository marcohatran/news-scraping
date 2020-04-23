# -*- coding: utf-8 -*-
import scrapy
import json

import modules.timeConverter as time


class DantriSpider(scrapy.Spider):
    name = 'dantri'
    allowed_domains = ['dantri.com.vn']

    def __init__(self, crawlMode='', **kwargs):
        super().__init__(**kwargs)
        self.crawlMode = crawlMode
        if crawlMode is 'update' or crawlMode is '':
            self.crawlMode = 'Update'

        self.articleCount = 0

    def start_requests(self):
        # return [scrapy.Request("https://dantri.com.vn/video/giai-phap-tan-dung-nguon-lao-dong-cao-tuoi-o-han-quoc-108264.htm", callback=self.parse_video)]
        # return [scrapy.Request("https://dantri.com.vn/xa-hoi/chiem-nguong-ngoi-dinh-hon-300-nam-tuoi-dep-nhat-xu-doai-20191016222010573.htm", callback=self.parse_article)]
        # return [scrapy.Request("https://dulich.dantri.com.vn/du-lich/hue-tien-phong-dua-he-thong-xe-dap-thong-minh-phuc-vu-du-khach-nguoi-dan-20191013102955719.htm", callback=self.parse_article)]
        # return [scrapy.Request("https://dantri.com.vn/the-gioi/co-gai-thuy-dien-goc-viet-va-uoc-mong-chay-bong-tim-cha-me-sau-22-nam-20191003144459720.htm", callback=self.parse_article)]
        return [scrapy.Request("https://dantri.com.vn/", callback=self.logged_in)]

    def logged_in(self, response):
        urls = ['https://dantri.com.vn/su-kien.htm',
                'https://dantri.com.vn/xa-hoi.htm',
                'https://dantri.com.vn/the-gioi.htm',
                'https://dantri.com.vn/the-thao.htm',
                'https://dantri.com.vn/giao-duc-khuyen-hoc.htm',
                'https://dantri.com.vn/tam-long-nhan-ai.htm',
                'https://dantri.com.vn/kinh-doanh.htm',
                'https://dantri.com.vn/bat-dong-san.htm',
                'https://dantri.com.vn/van-hoa.htm',
                'https://dantri.com.vn/giai-tri.htm',
                'https://dantri.com.vn/phap-luat.htm',
                'https://dantri.com.vn/nhip-song-tre.htm',
                'https://dantri.com.vn/suc-khoe.htm',
                'https://dantri.com.vn/suc-manh-so.htm',
                'https://dantri.com.vn/o-to-xe-may.htm',
                'https://dantri.com.vn/tinh-yeu-gioi-tinh.htm',
                'https://dantri.com.vn/chuyen-la.htm',
                'https://dantri.com.vn/doi-song.htm',
                'https://dantri.com.vn/ban-doc.htm',
                'https://dantri.com.vn/khoa-hoc-cong-nghe.htm']

        # scrape article
        for url in urls:
            yield scrapy.Request(url, callback=self.parse)

        # Bo do khong co ld+json phu hop
        # scrape travel section
        # yield scrapy.Request("https://dulich.dantri.com.vn/", callback=self.parse_travel_nav)

        # scrape video
        # yield scrapy.Request("https://dantri.com.vn/video-page.htm", self.parse_video_passer)

    def parse(self, response):
        for href in response.xpath('//*[@data-linktype="newsdetail"]/@href'):
            try:
                yield response.follow(href, callback=self.parse_article)
            except Exception:
                self.logger.error("ERROR: ", exc_info=True)
                continue

        next_page = response.xpath(
            '//*[@id="html"]/body//div[@class ="fr"][1]//@href')[0]
        if next_page is not None:
            yield response.follow(next_page, callback=self.parse)

    def parse_travel_nav(self, response):
        for href in response.xpath('//li[@class="normal"]/a/@href').getall()[1:6]:
            try:
                url = "https://dulich.dantri.com.vn"+href
                yield scrapy.Request(url, callback=self.parse_travel, meta={'index': 1, 'segment': url})
            except Exception:
                self.logger.error("ERROR: ", exc_info=True)
                continue

    def parse_travel(self, response):
        index = response.meta['index']
        segment = response.meta['segment']

        if index == 101 or response.xpath('//ul[@class="listcate fl"]/li[@class = "normal"]//@href').get() is None:
            return

        if index == 1:
            href = response.xpath('//li[@class = "top"]//@href').get()
            yield response.follow(href, self.parse_article)
        for href in response.xpath('//ul[@class="listcate fl"]/li[@class = "normal"]//@href'):
            try:
                yield response.follow(href, self.parse_article)
            except Exception:
                self.logger.error("ERROR: ", exc_info=True)
                continue

        index += 1
        next_page = segment.replace('.htm', '') + "/trang-" + \
            str(index)+".htm"
        yield scrapy.Request(next_page, self.parse_travel, meta={'index': index, 'segment': segment})

    def parse_video_passer(self, response):
        PAGE_CAP = 101
        for page in range(1, PAGE_CAP):
            try:
                video_getter = "https://dantri.com.vn/video/latest/0-" + \
                    str(page)+"-1000-0.htm"
                yield scrapy.Request(video_getter, callback=self.parse_video)
            except Exception:
                self.logger.error("ERROR: ", exc_info=True)
                continue

    def parse_video(self, response):
        videos = ''
        for a in response.xpath('//text()').getall():
            videos += a
        if videos == None:
            return

        video_dict = json.loads(videos)
        for vid in video_dict:
            try:
                yield {'video-' + str(vid.get('Id')): vid}
            except Exception:
                self.logger.error("ERROR: ", exc_info=True)
                continue

    def parse_article(self, response):
        article = {}

        # get ld_json
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
            'category': response.xpath('//a[@class = "breadcrumbitem1"][contains(@href, "htm")]/span/text()').get(),
            'organization': 'dân trí',
            'url': response.url,
            'related_urls': response.xpath('//div[@class = "article-oldnew"]//div/div[@class = "article-oldnew-img"]/a/@href').getall()
        }
        article.update(elems)

        # get content
        content = ''
        for text in response.xpath('//*[@id="divNewsContent"]/p/text()').getall():
            content += text.strip()
        for text in response.xpath('//*[@class = "detail-content"]/p/text()').getall():
            content += text.strip()
        for text in response.xpath('//div[@class="e-body"]//p/text()').getall():
            content += text.strip()
        article.update({'content': content})

        word_count = len(content.split())
        article.update({'word_count': word_count})

        # get image url
        images = {}
        index1 = index2 = 0
        for index1, src in enumerate(response.xpath('//*[@id="divNewsContent"]//img/@src').getall(), 1):
            images.update({'image' + str(index1): src})
        for index2, src in enumerate(response.xpath('//*[@class = "detail-content"]//img/@src').getall(), index1 + 1):
            images.update({'image' + str(index2): src})
        for index3, src in enumerate(response.xpath('//div[@class="e-body"]//figure[contains(@class,"image")]//@src').getall(), index2 + 1):
            images.update({'image' + str(index3): src})

        article.update({'image-urls': images})

        # get hashtags
        hashtags = {}
        for index, href in enumerate(response.xpath('//span[@class = "news-tags-item"]/a/@href').getall(), 1):
            hashtags.update({'tag'+str(index): href})
        article.update({'hash-tags': hashtags})

        # get video url
        videos = {}
        for index, src in enumerate(response.xpath('//div[@class="e-body"]/figure[@class = "video"]//@data-src').getall(), 1):
            videos.update({'video' + str(index): "vcdn.dantri.com.vn/" + src})
        article.update(videos)

        # get likes
        id = response.xpath('//*[@id="hdNewsId"]/@value').get()
        if id is not None:
            like_request = "https://www.facebook.com/v2.3/plugins/like.php?action=like&app_id=164035690775918&channel=https%3A%2F%2Fstaticxx.facebook.com%2Fconnect%2Fxd_arbiter.php%3Fversion%3D44%23cb%3Df31c1be4fdc1a28%26domain%3Ddantri.com.vn%26origin%3Dhttps%253A%252F%252Fdantri.com.vn%252Ff3a046e102e74f4%26relation%3Dparent.parent&container_width=0&href=https%3A%2F%2Fdantri.com.vn%2Fnews-" + \
                id+".htm&layout=button_count&locale=vi_VN&sdk=joey&share=false&show_faces=false&size=small"
        else:
            id = response.xpath('//*[@id="hidDistID"]/@value').get()
            if id is not None:
                like_request = "https://www.facebook.com/plugins/like.php?href="+response.url + \
                    "&send=false&share=true&layout=standard&width=450&show_faces=false&action=like&colorscheme=light&font&height=35&"
            else:
                pv1 = response.url.find('.htm')
                pv2 = response.url.find('-', pv1-20) + 1
                id = response.url[pv2:pv1]
                like_request = "https://www.facebook.com/v2.3/plugins/like.php?action=like&app_id=164035690775918&channel=https%3A%2F%2Fstaticxx.facebook.com%2Fconnect%2Fxd_arbiter.php%3Fversion%3D44%23cb%3Df322cc0314d7894%26domain%3Ddantri.com.vn%26origin%3Dhttps%253A%252F%252Fdantri.com.vn%252Ffe7c5846d65f58%26relation%3Dparent.parent&container_width=0&href=https%3A%2F%2Fdantri.com.vn%2Fnews-" + \
                    id+".htm&layout=button_count&locale=vi_VN&sdk=joey&share=false&show_faces=false"
        yield scrapy.Request(like_request, callback=self.parse_likes, meta={'article': article, 'id': id})

    def parse_likes(self, response):
        article = response.meta['article']
        id = response.meta['id']

        likes = response.xpath(
            '//button[@type="submit"]/div/span[3]/text()').get()
        if likes is not None:
            strings = [s for s in likes.split() if s.isdigit()]
            if len(strings) != 0:
                likes = strings[0]
            else:
                likes = '0'
        else:
            likes = '0'

        article.update({'likes-counter': likes})

        CMT_CAP = 10000
        cmt_request = "https://apicomment.dantri.com.vn/api/comment/list/1-" + \
            id+"-0-0-"+str(CMT_CAP)+".htm"
        yield scrapy.Request(cmt_request, callback=self.parse_comments, meta={'article': article})

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
                try:
                    cmt_dict.append(json.loads(string))
                except:
                    pass
                string = ''

        cmt_count = len(cmt_dict)
        for cmt in cmt_dict:
            cmt['CreatedDate'] = time.comment_time(cmt['CreatedDate'])
            cmt_count += cmt.get('ReplyCount')
        article.update({'comments-count': cmt_count, 'comments': cmt_dict})
        self.logger.info("#%d: Scraping %s", self.articleCount,
                         article.get('url'))
        self.articleCount += 1
        return article
