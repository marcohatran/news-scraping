import scrapy
from ..items import News, QuoteItem
import json
import requests
class test(scrapy.Spider):
    name='vdtuoitre'
    #allowed_domains = ['vnexpress.net']
    start_urls=['https://tv.tuoitre.vn/the-gioi-muon-mau.htm']
    def parse(self,response):
        urls = ['https://tv.tuoitre.vn/tin-nong.htm',
                'https://tv.tuoitre.vn/dac-sac.htm',
                'https://tv.tuoitre.vn/the-gioi-muon-mau.htm',
                'https://tv.tuoitre.vn/chuyen-doi-thuong.htm',
                'https://tv.tuoitre.vn/ban-co-biet.htm',
                'https://tv.tuoitre.vn/the-thao.htm',
                'https://tv.tuoitre.vn/giai-tri.htm',
                'https://tv.tuoitre.vn/hai-huoc.htm']
        for url in urls:
            yield scrapy.Request(url, callback=self.parse_start)

    def parse_start(self,response):
        alllink = response.xpath('//div[@id="autonextNoiBat01"]/div/ul/li/h3/a/@href').getall()
        alllink2 = response.xpath('//ul[@class="list-program"]/li/h3/a/@href').getall()
        for link in alllink:
            #print(link)https://tv.tuoitre.vn/len-ban-ma-tuy-qua-khe-cua-76286.htm
            yield scrapy.Request('https://tv.tuoitre.vn' + link, callback=self.parse_video)
        for link in alllink2:
            yield scrapy.Request('https://tv.tuoitre.vn' + link, callback=self.parse_video)


    def parse_video(self, response):
        video = {}

        link_video = response.xpath('//div[@class="fr description-video"]/h2/a/@href').getall()
        video.update({'link_video': link_video})

        title_video = response.xpath('//div[@class="fr description-video"]/h2/a/text()').getall()
        video.update({'title_video': title_video})
        content_video = response.xpath('//div[@class="fr description-video"]/p[@class="sapo-video"]/text()').getall()
        video.update({'content_video': content_video})
        author_video = response.xpath('//div[@class="fr description-video"]/p[@class="authorvideo"]/text()').getall()
        video.update({'author_video': author_video})

        #get meta
        video.update({'meta-description' : response.xpath("//head/meta[@name='description']/@content").get()})
        video.update({'meta-keywords' : response.xpath("//head/meta[@name='keywords']/@content").get()})
        video.update({'meta-title' : response.xpath("//head/meta[@name='title']/@content").get()})
        video.update({'meta-copyright' : response.xpath("//head/meta[@name='copyright']/@content").get()})
        video.update({'meta-author' : response.xpath("//head/meta[@name='author']/@content").get()})
        video.update({'meta-article:publisher' : response.xpath("//head/meta[@property='article:publisher']/@content").get()})



        objectid = response.xpath('//div[@class="aspNetHidden"]/input[@id="hidVideoId"]/@value').get()
        cmt_resquest = 'https://id.tuoitre.vn/api/getlist-comment.api?pageindex=1'+ '&objId='+ objectid

        yield scrapy.Request(cmt_resquest,callback=self.parse_comment_video,meta={'data': video})

        return video
    
    def parse_comment_video(self,response):
        str1 = ''
        for text in response.xpath('//text()').getall():
            str1 += text
        dict = json.loads(str1)
        totalcmt =len(dict)
        
        log1 =  response.meta['data']
        log1.update({'comment': dict})

        yield log1
