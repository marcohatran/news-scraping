import scrapy
import json

import modules.timeConverter as time


class SohaSpider(scrapy.Spider):
    name = 'soha'
    allowed_domains = ['soha.vn']

    def __init__(self, crawlMode='', **kwargs):
        super().__init__(**kwargs)
        self.crawlMode = crawlMode
        if crawlMode is 'update' or crawlMode is '':
            self.crawlMode = 'Update'

        self.articleCount = 0

    def start_requests(self):
        return [scrapy.Request("https://soha.vn/", callback=self.logged_in)]

    def logged_in(self, response):
        urls = [
            "https://soha.vn/thoi-su.htm",
            "https://soha.vn/kinh-doanh.htm",
            "https://soha.vn/quoc-te.htm",
            "https://soha.vn/quan-su.htm",
            "https://soha.vn/cu-dan-mang.htm",
            "https://soha.vn/giai-tri.htm",
            "https://soha.vn/phap-luat.htm",
            "https://soha.vn/song-khoe.htm",
            "https://soha.vn/cong-nghe.htm",
            "https://soha.vn/doi-song.htm",
            "https://soha.vn/kham-pha.htm",
        ]
        # scrape articles
        for url in urls:
            yield scrapy.Request(url, self.parse, meta={'index': 3})

        # scrape sport articles
        yield scrapy.Request("https://soha.vn/the-thao.htm", callback=self.parse_sport_nav)

        # scrape videos - Bo do khong co ld+json
        # yield scrapy.Request("https://soha.vn/video.htm", callback=self.parse_video_passer)

    def parse(self, response):
        if response.xpath('//@href').get() is None:
            return
        for href in response.xpath('//div[@class = "info-new-cate elp-list"]/h3/a/@href'):
            try:
                yield response.follow(href, callback=self.parse_article, meta={'atc_type': 'normal'})
            except Exception:
                self.logger.error("ERROR: ", exc_info=True)
                continue

        if 'timeline' not in response.url:
            section_id = response.xpath('//*[@id="hdZoneId"]/@value').get()
        else:
            section_id = response.meta['section_id']

        index = response.meta['index']
        next_page = "https://soha.vn/timeline/" + \
            section_id + "/trang-"+str(index)+".htm"
        yield scrapy.Request(next_page, callback=self.parse, meta={'index': index+1, 'section_id': section_id})

    def parse_article(self, response):
        atc_type = response.meta['atc_type']

        article = {}

        # get ld_json
        if atc_type == 'normal':
            ld_json = response.xpath(
                '//*[@id="Head1"]//script[contains(text(),"NewsArticle")]/text()').get()
            ld_json_dict = json.loads(ld_json)
            ld_json_dict = time.timestamp_converter(ld_json_dict)
            article.update(ld_json_dict)

        try:
            cate_json = cate = response.xpath(
                '//script[contains(text(), "BreadcrumbList")]/text()').get().strip()
            cate_json = json.loads(cate_json)
            category = cate_json.get('itemListElement')[
                1].get('item').get('name')
            article.update({'category': category})
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
            'organization': 'soha',
            'url': response.url,
            # 'related_urls': response.xpath('//div[@class = "article-oldnew"]//div/div[@class = "article-oldnew-img"]/a/@href').getall()
        }
        article.update(elems)

        # get content
        content = ''
        for text in response.xpath('//div[@class = "clearfix news-content"]/p/text()').getall():
            content += text
        article.update({'content': content})

        word_count = len(content.split())
        article.update({'word_count': word_count})

        # get image url
        images = {}
        for index, src in enumerate(response.xpath('//div[@class = "clearfix news-content"]/div[@type = "Photo"]//@src').getall(), 1):
            images.update({'image' + str(index): src})
        article.update({'image-urls': images})

        # get likes,comments
        yield scrapy.Request("https://sharefb.cnnd.vn/?urls="+response.url, callback=self.parse_interations, headers={'Accept': 'application/json, text/javascript, */*; q=0.01',
                                                                                                                      'Origin': 'https://soha.vn',
                                                                                                                      'Referer': response.url,
                                                                                                                      'Sec-Fetch-Mode': 'cors',
                                                                                                                      'User-Agent': 'Mozilla/5.0 (Windows 10 Win64 x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36'}, meta={'article': article, 'atc_type': atc_type})

    def parse_sport_nav(self, response):
        for href in response.xpath('//ul[@class = "sub-menu clearfix fr"]//li/a/@href').getall()[:5]:
            try:
                yield response.follow(href, self.parse_sport_passer)
            except Exception:
                self.logger.error("ERROR: ", exc_info=True)
                continue

    def parse_sport_passer(self, response):
        find_id = response.xpath(
            '//script[contains(text(),"zoneId")]/text()').get()
        pv1 = find_id.find('zoneId')
        pv2 = find_id[pv1:].find("'") + pv1 + 1
        pv3 = find_id[pv2:].find("'") + pv2
        section_id = find_id[pv2:pv3]
        page_index = 1
        page_url = "https://soha.vn/timeline_sport/" + \
            section_id+"/e0-trang-"+str(page_index)+".htm"
        yield scrapy.Request(page_url, callback=self.parse_sport, meta={'section_id': section_id, 'page_index': page_index})

    def parse_sport(self, response):
        if response.xpath('//@href').get() is None:
            return
        for href in response.xpath('//li[@class="clearfix"]/a/@href'):
            try:
                yield response.follow(href, callback=self.parse_article, meta={'atc_type': "sport"})
            except Exception:
                self.logger.error("ERROR: ", exc_info=True)
                continue

        section_id = response.meta['section_id']
        page_index = response.meta['page_index'] + 1

        page_url = "https://soha.vn/timeline_sport/" + \
            section_id+"/e0-trang-"+str(page_index)+".htm"
        yield scrapy.Request(page_url, callback=self.parse_sport, meta={'section_id': section_id, 'page_index': page_index})

    def parse_video_passer(self, response):
        PAGE_CAP = 595
        for page in range(1, PAGE_CAP):
            video_getter = "https://s1.soha.vn/video/latest/0-" + \
                str(page)+"-1000-0.htm"
            yield scrapy.Request(video_getter, callback=self.parse_video)

    def parse_video(self, response):
        videos = ''
        for a in response.xpath('//text()').getall():
            videos += a
        if videos == 'null':
            return

        video_dict = []
        check = 0
        string = ''
        for a in videos:
            if a is '{':
                check = 1
            if check is 1:
                string += a
            if a is '}':
                string += a
                check = 0
                try:
                    dict = json.loads(string)
                    dict['FileName'] = "http://vcplayer.mediacdn.vn/1.1?_site=sohanews&vid=sohanews/" + dict['FileName']
                    video_dict.append(dict)
                except:
                    pass
                string = ''

        for vid in video_dict:
            yield {'video-' + str(vid['Id']): vid}

    def parse_interations(self, response):
        article = response.meta['article']
        atc_type = response.meta['atc_type']

        string = ''
        for a in response.xpath('//text()').getall():
            string += a
        if string == None:
            string = '[{ }]'
        inter_dict = json.loads(string[1:len(string) - 1])
        if atc_type == "normal":
            del inter_dict["url"]
        article.update({'interactions': inter_dict})

        self.logger.info("#%d: Scraping %s", self.articleCount,
                         article.get('url'))
        self.articleCount += 1
        return article
