import scrapy
import json
from scrapy_splash import SplashRequest


class DantriSpider(scrapy.Spider):
    name = 'video-test'
    allowed_domains = ['nguoiduatin.vn']

    def start_requests(self):
        #   pass
        yield SplashRequest("https://www.nguoiduatin.vn/phan-no-chung-kien-canh-giao-vien-chu-nhiem-bat-tai-danh-dap-hang-loat-hoc-sinh-lop-2-a451647.html", args={'wait': 15})
    # yield scrapy.Request("https://api.news.zing.vn/api/comment.aspx?action=get&id=998037", callback=self.parse_cmt)
    # yield SplashRequest("https://api.news.zing.vn/api/comment.aspx?action=get&id=998037", callback=self.parse_cmt,args={"wait" : 0.5})

    def parse(self, response):
        yield{
            'video-src': response.xpath('//*[@class = "vmp-tech"]/@src').get()
        }
