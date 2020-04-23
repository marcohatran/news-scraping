import scrapy
import json
import modules.timeConverter as time


class ThanhnienSpider(scrapy.Spider):
    name = 'thanhnien'
    allowed_domains = ['thanhnien.vn']

    def __init__(self, crawlMode='', **kwargs):
        super().__init__(**kwargs)
        self.crawlMode = crawlMode
        if crawlMode is 'update' or crawlMode is '':
            self.crawlMode = 'Update'

        self.articleCount = 0

    def start_requests(self):
        return [scrapy.Request("https://thanhnien.vn", callback=self.logged_in)]
        # return [scrapy.Request("https://thanhnien.vn/tai-chinh-kinh-doanh/mui-ne-lao-dao-vi-thieu-khach-nga-516854.html", callback=self.parse_article)]
        # return [scrapy.Request("https://thanhnien.vn/van-hoa/luat-hong-lan-lon-tien-su-tien-chua-1134512.html", callback=self.parse_article, meta={'atc_type': "normal"})]
        # return [scrapy.Request("https://xe.thanhnien.vn/thi-truong-xe/ford-trieu-hoi-gan-20000-xe-ban-tai-ranger-nguy-co-chay-do-chap-dien-20442.html", callback=self.parse_article, meta={'atc_type': "video"})]
        # return [scrapy.Request("https://thethao.thanhnien.vn/bong-da-viet-nam/tuyen-viet-nam-giu-cu-ly-doi-hinh-xuat-sac-va-hau-ve-tan-cong-qua-hay-106518.html", callback=self.parse_article, meta={'atc_type': "sport"})]

    def logged_in(self, response):
        urls = [
            "https://thanhnien.vn/thoi-su/",
            "https://thanhnien.vn/the-gioi/",
            "https://thanhnien.vn/tai-chinh-kinh-doanh/",
            "https://thanhnien.vn/doi-song/",
            "https://thanhnien.vn/van-hoa/",
            "https://thanhnien.vn/gioi-tre/",
            "https://thanhnien.vn/giao-duc/",
            "https://thanhnien.vn/suc-khoe/",
            "https://thanhnien.vn/du-lich/",
            "https://thanhnien.vn/cong-nghe/",
        ]

        # scrape articles
        for url in urls:
            yield scrapy.Request(url, self.parse, meta={'page_index': 1, 'cate': 'normal'})

        # scrape sport articles
        yield scrapy.Request("https://thethao.thanhnien.vn/", callback=self.parse_nav, meta={'cate': 'sport'})

        # scrape cars articles
        yield scrapy.Request("https://xe.thanhnien.vn/", callback=self.parse_nav, meta={'cate': 'other'})

        # scrape game articles
        yield scrapy.Request("https://game.thanhnien.vn/", callback=self.parse_nav, meta={'cate': 'other'})

        # scrape video articles
        yield scrapy.Request("https://video.thanhnien.vn/", callback=self.parse_nav, meta={'cate': 'other'})

    def parse_nav(self, response):
        cate = response.meta['cate']
        if cate == "other":
            parser = self.parse
        if cate == "sport":
            parser = self.parse_sport_passer

        for href in response.xpath('//nav[@class = "site-header__nav"]/a/@href'):
            try:
                yield response.follow(href, parser, meta={'page_index': 1, 'cate': cate})
            except Exception:
                self.logger.error("ERROR: ", exc_info=True)
                continue

    def parse_sport_passer(self, response):
        for segment in response.xpath('//header[@class="heading"]/h3/a/@href'):
            try:
                yield response.follow(segment, self.parse, meta=response.meta)
            except Exception:
                self.logger.error("ERROR: ", exc_info=True)
                continue

    def parse(self, response):
        page_index = response.meta['page_index']
        cate = response.meta['cate']

        if page_index == 1:
            section = response.url
        else:
            section = response.meta['section']

        if cate == 'normal':
            if page_index == 1:
                yield response.follow(response.xpath('//div[@class="l-content"]/div[@class="highlight"]//a/@href').get(), self.parse_article, meta={'atc_type': 'normal'})
                for href in response.xpath('//div[@class="l-content"]/div[@class="feature"]//h2/a/@href').getall():
                    try:
                        yield response.follow(href, self.parse_article)
                    except Exception:
                        self.logger.error("ERROR: ", exc_info=True)
                        continue
            if page_index is not 1 and section is response.url or response.xpath('//div[@class="l-content"]/div[@class="feature"]//h2/a/@href').get() is None:
                return
            for href in response.xpath('//div[@class = "relative"]/article/a/@href'):
                try:
                    yield response.follow(href, callback=self.parse_article)
                except Exception:
                    self.logger.error("ERROR: ", exc_info=True)
                    continue
        if cate == 'other':
            if page_index == 1:
                for href in response.xpath('//article[@class="spotlight"]/a/@href'):
                    try:
                        yield response.follow(href, self.parse_article)
                    except Exception:
                        self.logger.error("ERROR: ", exc_info=True)
                        continue
            if response.xpath('//article[@class="clearfix"]/a/@href').get() is None:
                return
            for href in response.xpath('//article[@class="clearfix"]/a/@href'):
                try:
                    yield response.follow(href, self.parse_article)
                except Exception:
                    self.logger.error("ERROR: ", exc_info=True)
                    continue
        if cate == 'sport':
            if page_index == 1:
                for href in response.xpath('//section[@class="highlight clearfix"]//header/a/@href'):
                    try:
                        yield response.follow(href, self.parse_article)
                    except Exception:
                        self.logger.error("ERROR: ", exc_info=True)
                        continue
            if response.xpath('//div[@class="timeline"]/nav//a[@id="ctl00_main_ContentList1_pager_nextControl"]/@href').get() is None:
                return
            for href in response.xpath('//div[@class="timeline"]//article//h2/a/@href'):
                try:
                    yield response.follow(href, self.parse_article)
                except Exception:
                    self.logger.error("ERROR: ", exc_info=True)
                    continue

        next_page = section + "trang-"+str(page_index+1)+".html"
        yield scrapy.Request(next_page, callback=self.parse, meta={'page_index': page_index+1, 'section': section, 'cate': cate})

    def parse_article(self, response):
        article = {}

        # get ld_json
        try:
            ld_json = response.xpath(
                "//script[contains(text(),'NewsArticle')]/text()").get()
            ld_json_dict = json.loads(ld_json)[0]
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
            'category': response.xpath('//h2[@class = "headline"]/a/text()').get(),
            'organization': 'thanh niên',
            'url': response.url,
            # 'related_urls': response.xpath('//div[@class = "article-oldnew"]//div/div[@class = "article-oldnew-img"]/a/@href').getall()
        }
        article.update(elems)

        # get video url
        videos = []

        try:
            url_finder = response.xpath(
                '//figure[@itemprop = "associatedMedia"]/script/text()').get()
            pv1 = url_finder.find("src")
            pv2 = url_finder[pv1:].find('"') + pv1+1
            pv3 = url_finder[pv2:].find('"') + pv2
            video_url = url_finder[pv2:pv3]
            videos.append(video_url)
        except:
            pass

        video_url = response.xpath(
            '//table[@class="video"]//@data-video-src').get()
        videos.append(video_url)

        article.update({'videos-url': videos})

        # get content
        content = ''
        for text in response.xpath('//div[@id="abody"]//p[contains(@style,"margin")or contains(@style,"text")]/text()').getall():
            content += text.strip()
        for text in response.xpath('//*[@id="abody"]//div/text()').getall():
            content += text.strip()
        article.update({'content': content})

        word_count = len(content.split())
        article.update({'word_count': word_count})

        # get image url
        images = {}
        ava_index = 0
        for ava_index, src in enumerate(response.xpath('//*[@id="contentAvatar"]//a/img/@src').getall(), 1):
            images.update({'image' + str(ava_index): src})
        index = ava_index + 1
        for index, src in enumerate(response.xpath('//*[@class="imagefull"]//@data-src').getall(), index):
            images.update({'image' + str(index): src})

        article.update({'image-urls': images})

        # get comments
        comments_count = response.xpath('//*[@id="commentcount"]/text()').get()
        article.update({'comments-count': comments_count})
        comments = []

        for comment in response.xpath('//*[@id="commentcontainer"]/div'):
            primary_comment = comment.xpath(
                './div[@class = "primary-comment"]')
            primary_ava = primary_comment.xpath(
                './/div[@class = "ava"]/img/@data-src').get()
            primary_user = primary_comment.xpath(
                './/div[@class = "data"]/div[@class = "meta"]/h4/text()').get()
            if primary_user is not None:
                primary_user = primary_user.strip()
            primary_geo = primary_comment.xpath(
                './/div[@class = "data"]/div[@class = "meta"]/time/text()').get()
            if primary_geo is not None:
                primary_geo = primary_geo.strip()
            primary_content = primary_comment.xpath(
                './/div[@class = "data"]/div[@class = "comment"]/text()').get()
            if primary_content is not None:
                primary_content = primary_content.strip()
            primary_time = primary_comment.xpath(
                './/div[@class = "meta"]/time/@rel').get()
            primary_likes = primary_comment.xpath(
                './/div[@class = "data"]/div[@class = "reply"]//a[@class = "likebtn"]//text()').get()
            if primary_likes is not None:
                primary_likes = primary_likes.strip()
                strings = [s for s in primary_likes.split() if s.isdigit()]
                if len(strings) != 0:
                    primary_likes = strings[0]
                else:
                    primary_likes = '0'

            secondary_dict = []
            counter = 0
            for counter, reply in enumerate(comment.xpath(
                    './/div[@class = "secondary-comment"]'), 1):
                secondary_ava = reply.xpath(
                    './/div[@class = "ava"]/img/@data-src').get()
                secondary_user = reply.xpath(
                    './/div[@class = "data"]/div[@class = "meta"]/h4/text()').get()
                if secondary_user is not None:
                    secondary_user = secondary_user.strip()
                secondary_geo = reply.xpath(
                    './/div[@class = "data"]/div[@class = "meta"]/time/text()').get()
                if secondary_geo is not None:
                    secondary_geo = secondary_geo.strip()
                secondary_content = reply.xpath(
                    './/div[@class = "data"]/div[@class = "comment"]/text()').get()
                if secondary_content is not None:
                    secondary_content = secondary_content.strip()
                secondary_time = reply.xpath(
                    './/div[@class = "meta"]/time/@rel').get()
                secondary_likes = reply.xpath(
                    './/div[@class = "data"]/div[@class = "reply"]//a[@class = "likebtn"]//text()').get()
                if secondary_likes is not None:
                    secondary_likes = secondary_likes.strip()
                    strings = [s for s in secondary_likes.split()
                               if s.isdigit()]
                    if len(strings) != 0:
                        secondary_likes = strings[0]
                    else:
                        secondary_likes = '0'

                secondary_dict.append({'SenderAvatar': secondary_ava,
                                       'SenderFullName': secondary_user,
                                       'PublishedGeo': secondary_geo,
                                       'CommentContent': secondary_content,
                                       'CreatedDate': secondary_time,
                                       'Liked': secondary_likes,
                                       'Replies-count': 0,
                                       'Replies': []})

            comments.append({
                'SenderAvatar': primary_ava,
                'SenderFullName': primary_user,
                'PublishedGeo': primary_geo,
                'CommentContent': primary_content,
                'CreatedDate': primary_time,
                'Liked': primary_likes,
                'Replies-count': counter,
                'Replies': secondary_dict if counter != 0 else None
            })
        article.update({'comments': comments})

        # get likes
        url = response.xpath(
            '//li[@class = "zalo-share-button"]/@data-href').get()
        if url is None:
            url = response.xpath('//li[@class="fb-share"]/a/@href').get()
        url = url.replace("=", "%3D")
        url = url.replace("/", "%2F")
        url = url.replace(":", "%3A")

        like_request = "https://www.facebook.com/v3.1/plugins/like.php?action=like&app_id=288067561729014&channel=https%3A%2F%2Fstaticxx.facebook.com%2Fconnect%2Fxd_arbiter.php%3Fversion%3D44%23cb%3Df1b1dac16a53484%26domain%3Dthanhnien.vn%26origin%3Dhttps%253A%252F%252Fthanhnien.vn%252Ff20b42488425504%26relation%3Dparent.parent&container_width=0&href=" + \
            url+"&layout=button_count&locale=en_US&sdk=joey&share=true&show_faces=false&size=large"
        yield scrapy.Request(like_request, callback=self.parse_likes, meta={'article': article})

    def parse_likes(self, response):
        article = response.meta['article']

        likes = response.xpath(
            '//button[@type="submit"]/div/span[3]/text()').get()
        if likes is None:
            likes = '0'

        article.update({'likes-counter': likes})
        self.logger.info("#%d: Scraping %s", self.articleCount,
                         article.get('url'))
        self.articleCount += 1
        return article
