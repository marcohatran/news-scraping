import pymongo
from pymongo import MongoClient
from datetime import datetime

import modules.MongoDB_driver_Duong as driver_duong
import modules.mongoDriver as driver_minh
# import module_news.MongoDB_driver as driver

from .config_enviroment import *


class MongoPipeline(object):
    def __init__(self):
        if AUTH_USERNAME != '' and HOST != '127.0.0.1':
            self.client = MongoClient(
                'mongodb://'+AUTH_USERNAME+':'+AUTH_PASSWORD+'@'+HOST+':'+PORT+'/'+DATABASE)
        else:
            self.client = MongoClient(
                'mongodb://' + HOST + ':' + PORT + '/' + DATABASE)
        self.database = 'articles'
        self.spiders_duong = [
            'afamily',
            'baomoi',
            'cafef',
            'tiin',
            'tuoitre',
            'yeah1',
            'vtv.vn',
            'saostar',
            'dspl',
            'vnexpress'
        ]
        self.spiders_minh = [
            'dantri',
            'kenh14',
            'soha',
            'nguoiduatin',
            'thanhnien',
            'zing',
            'viblo',
            'vietnamnet',
            'techtalk'
        ]

        self.organization = {
            'dantri': 'dân trí',
            'kenh14': 'kênh 14',
            'soha': 'soha',
            'nguoiduatin': 'người đưa tin',
            'thanhnien': 'thanh niên',
            'zing': 'zing',
            'viblo': 'viblo',
            'vietnamnet': 'vietnamnet',
            'techtalk': 'techtalk',
            'afamily': 'Afamily',
            'baomoi': 'Báo mới',
            'cafef': 'Cafef',
            'dspl': 'Đời sống pháp luật',
            'saostar': 'Saostar',
            'tiin': 'Tiin',
            'tuoitre': 'Tuổi trẻ',
            'vnexpress': 'Vnexpress',
            'vtv.vn': 'VTV',
            'yeah1': 'Yeah1'
        }

        self.dateLimit = 5  # Number of days to check
        self.tolerables = 0
        self.maxTolerables = 30
        self.last = None

    def process_item(self, item, spider):
        database = self.client[self.database]

        # print(self.last)
        if spider.crawlMode is not None:
            if spider.crawlMode is 'Update':
                if database['articles'].find_one({'organization': self.organization.get(spider.name)}) is not None:
                    if self.last is None:
                        self.last = database['articles'].find_one(
                            {'organization': self.organization.get(spider.name)}, sort=[('_id', pymongo.DESCENDING)])
                        if self.last is not None and self.last.get('date_published') is None:
                            self.last = None
                    try:
                        if (datetime.fromtimestamp(item.get('datePublished')) - datetime.fromtimestamp(self.last.get('date_published'))).days <= self.dateLimit:
                            self.tolerables += 1
                    except:
                        pass
                    print(self.tolerables)
                    if self.tolerables >= self.maxTolerables:
                        spider.crawler.engine.close_spider(
                            self, reason='duplicate')

        if spider.name in self.spiders_duong:
            driver_duong.insert_data_article(database, item)

        if spider.name in self.spiders_minh:
            driver_minh.insert_article(database, item, spider.name)

        return item
