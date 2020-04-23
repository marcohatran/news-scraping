from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import re
import scrapy
import json
class vdvnexpressclass(CrawlSpider):

    name = "vdvnexpress"            # define name of spider
    allowed_domains = ['video.vnexpress.net','sharefb.cnnd.vn','usi-saas.vnexpress.net','www.facebook.com']
    start_urls = ['https://video.vnexpress.net/']

    rules = (
        Rule(LinkExtractor(), callback='parse_item', follow=True),
    )

    def parse_item(self, response):
        #print(response.url)
        article = {}
        #get ld json
        try:
            ld_json = response.xpath('//head/script[@type="application/ld+json"]//text()').get()
            if ld_json == None:
                return ld_json == 0
            else:
                ld_json = ld_json
            article = json.loads(ld_json)
        except ValueError:
            return 0
        #get meta

        article.update({'meta-description' : response.xpath("//head/meta[@name='description']/@content").get()})
        article.update({'meta-keywords' : response.xpath("//head/meta[@name='keywords']/@content").get()})
        article.update({'meta-copyright' : response.xpath("//head/meta[@name='copyright']/@content").get()})
        article.update({'meta-author' : response.xpath("//head/meta[@name='author']/@content").get()})
        article.update({'meta-article:publisher' : response.xpath("//head/meta[@property='article:publisher_time']/@content").get()})
        article.update({'meta-article:author' : response.xpath("//head/meta[@property='article:author']/@content").get()})


        #title, link, author, content
        title = response.xpath('//div[@id="info_inner"]/h1[@class="title"]/text()').get()
        link = response.url
        article.update({'title': title, 'link': link})

        content =''
        author = ''
        text = response.xpath('//div[@id="info_inner"]/p[@class="author o_info"]/span/text()').get()
        if text == None:
            author = ''
        else:
            author += text.strip()
        article.update({'author' : author})
        text1 = response.xpath('//div[@id="info_inner"]/div[@class="lead_detail"]/text()').get()
        if text1 == None:
            content = ''
        else:
            content += text1.strip()
        article.update({'content' : content})

        #get comment

        id ={}


        objectid = response.xpath('//head/meta[@name="tt_article_id"]/@content').get()
        if objectid == None:
            return 0
        else:
            objectid = objectid
        siteid = response.xpath('//head/meta[@name="tt_site_id"]/@content').get()
        if siteid == None:
            return 0
        else:
            siteid = siteid
        categoryid = response.xpath('//head/meta[@name="tt_category_id"]/@content').get()
        if categoryid == None:
            return 0
        else:
            categoryid  = categoryid

        id.update({'objectid': objectid, 'siteid':siteid, 'categoryid':categoryid})


        #get total like
        like_request = "https://www.facebook.com/plugins/like.php?action=like&app_id=&channel=https%3A%2F%2Fstaticxx.facebook.com%2Fconnect%2Fxd_arbiter.php%3Fversion%3D44%23cb%3Df18c6c90e40dcec%26domain%3Dvideo.vnexpress.net%26origin%3Dhttps%253A%252F%252Fvideo.vnexpress.net%252Ffc8a4c1ee2b278%26relation%3Dparent.parent&container_width=450&href=" + response.url +"&layout=button_count&locale=vi_VN&sdk=joey&share=false&show_faces=false&size=large"
        yield scrapy.Request(like_request, callback=self.parse_like, meta={'article': article, 'id': id})
        #print(like_request)

        
        #get comment

    def parse_comment(self, response):
        str1 = ''
        for text in response.xpath('//text()').getall():
            str1 += text
        dict = json.loads(str1)
        totalcmt =len(dict)
        #print (d)
        log =  response.meta['data']
        log.update({'totalcmt': totalcmt, 'comment': dict})

        yield log

    def parse_like(self,response):
        log = response.meta['article']
        id = response.meta['id']

        likes = response.xpath('(//span[@id="u_0_3"]/text())|(//*[@id="u_0_4"]/text())').get()

        log.update({'likes-counter': likes})

        cmt_resquest = 'https://usi-saas.vnexpress.net/index/get?offset=0&limit=24&frommobile=0&sort=like&is_onload=1&objectid='+ id['objectid'] + '&objecttype=1&siteid='+ id['siteid']+ '&categoryid='+ id['categoryid']

        yield scrapy.Request(cmt_resquest,callback=self.parse_comment,meta={'data': log})