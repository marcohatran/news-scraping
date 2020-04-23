import scrapy
from scrapy.http import FormRequest
import json
import modules.timeConverter as time


class TechtalkSpider(scrapy.Spider):
    name = 'techtalk'
    allowed_domains = ['techtalk.vn']
    prefix = "techtalk.vn"

    def __init__(self, crawlMode='', **kwargs):
        super().__init__(**kwargs)
        self.crawlMode = crawlMode
        if crawlMode is 'update' or crawlMode is '':
            self.crawlMode = 'Update'

        self.articleCount = 0

    def start_requests(self):
        return [scrapy.Request("https://techtalk.vn", callback=self.logged_in)]
        # return [scrapy.Request("https://techtalk.vn/video-cam-xuc-khi-choi-lai-game-4-nut.html", callback=self.parse_article)]

    def logged_in(self, response):
        block_urls = [
            'https://techtalk.vn/resources',
            'https://techtalk.vn/tech',
        ]
        for url in block_urls:
            yield scrapy.Request(url, callback=self.parse_block)

        loop_urls = [
            'https://techtalk.vn/category/dev',
            'https://techtalk.vn/category/su-kien',
            'https://techtalk.vn/category/chuyen-gia-noi',
            'https://techtalk.vn/category/tam-su-coder'
        ]
        for url in loop_urls:
            yield scrapy.Request(url, callback=self.parse_loop)

    def parse_block(self, response):
        block = response.xpath(
            '//div[contains(@class, "wpb_column vc_column_container")]//div[@class = "wpb_wrapper"]/div/@class').get()
        block = block.split(' ')[1]
        current_page = 1
        for i in range(1, 500):
            frmdata = {"action": "td_ajax_block",
                       "td_current_page": str(current_page), "block_type": block}
            current_page += 1
            try:
                r = FormRequest(
                    'https://techtalk.vn/wp-admin/admin-ajax.php?td_theme_name=Newspaper&v=7.3', callback=self.parse, formdata=frmdata, meta={'stillCrawl': True})
                # self.logger.info(current_page)
                yield r
                if r.meta['stillCrawl'] is False:
                    break
            except:
                self.logger.error("ERROR: ", exc_info=True)
                continue

    def parse_loop(self, response):
        cate_id = response.xpath(
            '//body[contains(@class, "wpb-js-composer")]/@class').get()
        cate_id = cate_id.split(' ')[3].replace('category-', '')
        script = response.xpath(
            '//script[contains(text(), "loopState.max_num_pages")]').get()
        pv1 = script.find('loopState.max_num_pages = ')
        pv2 = pv1 + script[pv1:].find(';')
        max_pages = script[pv1:pv2]
        strings = [s for s in max_pages.split() if s.isdigit()]
        max_pages = strings[0]
        current_page = 1
        for i in range(1, int(max_pages) + 1):
            frmdata = {"action": "td_ajax_loop", "loopState[sidebarPosition]": '', "loopState[moduleId]": '1',
                       "loopState[currentPage]": str(current_page), "loopState[atts][category_id]": cate_id}
            current_page += 1
            try:
                r = FormRequest(
                    'https://techtalk.vn/wp-admin/admin-ajax.php?td_theme_name=Newspaper&v=7.3', callback=self.parse, formdata=frmdata, meta={'stillCrawl': True})
                yield r
                if r.meta['stillCrawl'] is False:
                    break
            except:
                self.logger.error("ERROR: ", exc_info=True)
                continue

    def parse(self, response):
        if response.xpath('//h3/a/@href').get() is None:
            response.meta['stillCrawl'] = False
        for href in response.xpath('//h3/a/@href').getall():
            try:
                href = href.replace("\\", '').replace('"', '')
                yield response.follow(href, callback=self.parse_article)
            except:
                self.logger.error("ERROR: ", exc_info=True)
                continue

    def parse_article(self, response):
        article = {}

        # get ld_json
        try:
            ld_json = response.xpath(
                '//script[contains(text(),"Article")]/text()').get()
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
            'organization': 'techtalk',
            'url': response.url,
            # 'related_urls': response.xpath('//div[@class = "article-oldnew"]//div/div[@class = "article-oldnew-img"]/a/@href').getall()
        }
        article.update(elems)
        try:
            article.update({'category': response.xpath(
                '//a[@class = "entry-crumb"]')[1].xpath('./span/text()').get()})
        except:
            pass

        # get content
        content = ''
        for text in response.xpath('//div[@class = "td-post-content"]//p/text()').getall():
            content += text.strip()
        article.update({'content': content})
        word_count = len(content.split())
        article.update({'word_count': word_count})

        # get image url
        images = {}
        for index, src in enumerate(response.xpath('//div[@class="td-post-content"]//*[contains(@class,"image") or contains(@class,"Image")]//@src').getall(), 1):
            images.update({'image' + str(index): src})
        article.update({'image-urls': images})

        # get video url
        videos = {}
        for index, src in enumerate(response.xpath('//div[@class="td-post-content"]//iframe/@src').getall(), 1):
            videos.update({'video' + str(index): src})
        article.update({'video urls': videos})

        # get hashtags
        hashtags = {}
        for index, href in enumerate(response.xpath('//ul[@class = "td-tags td-post-small-box clearfix"]//@href').getall(), 1):
            hashtags.update({'tag'+str(index): href})
        article.update({'hash-tags': hashtags})

        # get views
        views = response.xpath('//div[@class="td-post-views"]//text()').get()
        article.update({'views': views})

        # get likes
        like_request = "https://www.facebook.com/plugins/like.php?href="+response.url + \
            "&layout=button_count&show_faces=false&width=105&action=like&colorscheme=light&height=21"
        yield scrapy.Request(like_request, callback=self.parse_likes, meta={'article': article, 'url': response.url})

    def parse_likes(self, response):
        article = response.meta['article']
        url = response.meta['url']

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

        # self.logger.info("#%d: Scraping %s", self.articleCount,
        #                  article.get('url'))
        # self.articleCount += 1
        # return article

        # get related-urls
        request_url = "https://tr.topdevvn.com/recommend?t=url&c=8d6d4537822016fc85c592e82b08e72b"
        yield scrapy.Request(request_url,
                             callback=self.parse_related, meta={'article': article}, dont_filter=True, headers={'Referer': url,
                                                                                                                'Accept': '*/*',
                                                                                                                'Origin': 'https://techtalk.vn',
                                                                                                                'Sec-Fetch-Mode': 'cors',
                                                                                                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'})

    def parse_related(self, response):
        article = response.meta['article']

        try:
            related_urls = []
            body = response.xpath('//text()').get()
            dict = json.loads(body)
            jobs = dict['job']
            jobs = json.loads(jobs)
            for job in jobs:
                related_urls.append(job['site'])
            article.update({'related_urls': related_urls})
        except:
            pass

        self.logger.info("#%d: Scraping %s", self.articleCount,
                         article.get('url'))
        self.articleCount += 1
        return article
