import scrapy
import json
import modules.timeConverter as time


class VietnamnetSpider(scrapy.Spider):
    name = 'vietnamnet'
    allowed_domains = ['vietnamnet.vn/']

    # start_urls = [
    #     'https://vietnamnet.vn/vn/kinh-doanh/sasco-vao-top-5-cong-ty-uy-tin-nganh-ban-le-nam-2019-585891.html'
    # ]

    def __init__(self, crawlMode='', **kwargs):
        super().__init__(**kwargs)
        self.crawlMode = crawlMode
        if crawlMode is 'update' or crawlMode is '':
            self.crawlMode = 'Update'

        self.articleCount = 0

    def start_requests(self):
        return [scrapy.Request("https://vietnamnet.vn/", callback=self.logged_in)]
        # return [scrapy.Request("https://vietnamnet.vn/vn/kinh-doanh/sasco-vao-top-5-cong-ty-uy-tin-nganh-ban-le-nam-2019-585891.html", callback=self.parse_article)]
        # return [scrapy.Request("https://vietnamnet.vn/vn/kinh-doanh/sasco-vao-top-5-cong-ty-uy-tin-nganh-ban-le-nam-2019-585891.html", callback=self.parse_article)]

    def logged_in(self, response):
        urls = [
            'https://vietnamnet.vn/vn/thoi-su/',
            'https://vietnamnet.vn/vn/kinh-doanh/',
            'https://vietnamnet.vn/vn/giai-tri/',
            'https://vietnamnet.vn/vn/the-gioi/',
            'https://vietnamnet.vn/vn/giao-duc/',
            'https://vietnamnet.vn/vn/doi-song/',
            'https://vietnamnet.vn/vn/phap-luat/',
            'https://vietnamnet.vn/vn/the-thao/',
            'https://vietnamnet.vn/vn/cong-nghe/',
            'https://vietnamnet.vn/vn/suc-khoe/',
            'https://vietnamnet.vn/vn/bat-dong-san/',
            'https://vietnamnet.vn/vn/ban-doc/',
            'https://vietnamnet.vn/vn/oto-xe-may/',
            'https://vietnamnet.vn/vn/goc-nhin-thang/',
            'https://vietnamnet.vn/vn/ban-tron-truc-tuyen/',
            'https://vietnamnet.vn/vn/hotface/',
        ]
        for url in urls:
            segment = url + 'trang'
            yield scrapy.Request(segment + '1', meta={'pageIndex': 1, 'segment': segment})

    def parse(self, response):
        pageIndex = response.meta['pageIndex']
        segment = response.meta['segment']

        if response.xpath('//div[@class = "clearfix item"]/a/@href').get() is None:
            return
        for href in response.xpath('//div[@class = "clearfix item"]/a/@href'):
            try:
                yield response.follow(href, self.parse_articles)
            except Exception:
                self.logger.error("ERROR: ", exc_info=True)
                continue

        next_page_request = segment + str(pageIndex + 1)
        yield scrapy.Request(next_page_request, meta={'pageIndex': pageIndex + 1, 'segment': segment})

    def parse_articles(self, response):
        article = {}

        # get ld_json
        try:
            ld_json = response.xpath(
                "//script[contains(text(),'NewsArticle')]/text()").get()
            ld_json_dict = json.loads(ld_json)
            ld_json_dict = time.vietnamnet_timestamp(ld_json_dict)
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
            'category': response.xpath('//div[@class = "top-cate-head-title"]/a/text()').get(),
            'organization': 'vietnamnet',
            'url': response.url,
            'related_urls': response.xpath('//div[@class = "article-relate"]//a/@href').getall()
        }
        article.update(elems)

        # get content
        content = ''
        for text in response.xpath('//div[@id = "ArticleContent"]//p/text()').getall():
            content += text.strip()
        if content == '':
            for text in response.xpath('//div[@class = "Magazine-Acticle EMA2018"]//p/text()').getall():
                content += text.strip()

        article.update({'content': content})

        word_count = len(content.split())
        article.update({'word_count': word_count})

        # get image url
        images = {}
        for index, src in enumerate(response.xpath('//div[@id = "ArticleContent"]//*[contains(@class,"image") or contains(@class,"Image")]//@src').getall(), 1):
            images.update({'image' + str(index): src})
        article.update({'image-urls': images})

        # get hashtags
        hashtags = {}
        for index, href in enumerate(response.xpath('//div[@class="tagBoxContent"]//@href').getall(), 1):
            hashtags.update({'tag'+str(index): href})
        article.update({'hash-tags': hashtags})

        # get video url
        videos = {}
        for index, src in enumerate(response.xpath('//iframe[contains(@src,"embed.vietnamnettv.vn/v")]/@src').getall(), 1):
            videos.update({'video' + str(index): src})
        article.update(videos)

        article_id = response.xpath(
            '//div[@class = "fmsidWidgetLike"]/@data-id').get()

        # get likes
        like_request = "https://www.facebook.com/plugins/like.php?action=like&app_id=&channel=https%3A%2F%2Fstaticxx.facebook.com%2Fconnect%2Fxd_arbiter.php%3Fversion%3D44%23cb%3Df1e420bc40a52c%26domain%3Dvietnamnet.vn%26origin%3Dhttps%253A%252F%252Fvietnamnet.vn%252Ff546fb88125%26relation%3Dparent.parent&container_width=83&href=" + \
            response.url + "&layout=button_count&locale=vi_VN&sdk=joey&share=true&show_faces=false&size=small"
        yield scrapy.Request(like_request, callback=self.parse_likes, meta={'article': article, 'article_id': article_id})

    def parse_likes(self, response):
        article = response.meta['article']
        article_id = response.meta['article_id']
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
        if article_id is None:
            self.logger.info("#%d: Scraping %s", self.articleCount,
                             article.get('url'))
            self.articleCount += 1
            return article

        cmt_request = "https://i.vietnamnet.vn/jsx/interaction/getInteraction/data.jsx?objkey=vietnamnet.vn_" + "/vn/_" + article_id
        yield scrapy.Request(cmt_request, callback=self.parse_comments, meta={'article': article})

    def parse_comments(self, response):
        article = response.meta['article']

        string = ''
        for a in response.xpath('//text()').getall():
            string += a

        string = string.replace('retvar=', '')

        comment_data = json.loads(string)
        comments_list = comment_data.get('comments')
        if comments_list is not None and len(comments_list) is not 0:
            for comment in comments_list:
                comment['Liked'] = comment.pop('like')
                comment['SenderFullName'] = comment.pop('fullname')
                comment['CommentContent'] = comment.pop('content')
                comment['CreatedDate'] = time.comment_time(
                    comment.pop('created_at'))
                comment['Replies'] = comment.pop('replies')
                if comment['Replies'] is not None:
                    for reply in comment['Replies']:
                        reply['Liked'] = reply.pop('like')
                        reply['SenderFullName'] = reply.pop('fullname')
                        reply['CommentContent'] = reply.pop('content')
                        reply['CreatedDate'] = time.comment_time(
                            reply.pop('created_at'))
                        reply['Replies'] = reply.pop('replies')

        cmt_count = comment_data.get('totalrecord')
        article.update({'comments-count': cmt_count,
                        'comments': comments_list})

        self.logger.info("#%d: Scraping %s", self.articleCount,
                         article.get('url'))
        self.articleCount += 1
        return article
