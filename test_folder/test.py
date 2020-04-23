from ..items import DmozItem
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import re
import scrapy
import json

class Test(CrawlSpider):
    name = "test"
    allowed_domains = ['baomoi.com','sharefb.cnnd.vn']
    start_urls = ['https://baomoi.com/the-gioi.epi/']

    rules = (
        Rule(LinkExtractor(), callback='parse_item', follow=True),
    )


    def parse_item(self, response):
        item = DmozItem()
        item['title'] =response.xpath('//div[@class="article"]/h1[@class="article__header"]/text()').get()
        item['link'] = response.url
        yield item