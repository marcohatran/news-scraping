from pymongo import MongoClient
import modules.mongoDriver as driver
import os
from .config_enviroment import *


class MongoUploadPipeline(object):
    def __init__(self):
        self.client = MongoClient(
            'mongodb://'+AUTH_USERNAME+':'+AUTH_PASSWORD+'@'+HOST+':'+PORT+'/'+DATABASE)
        # self.client = MongoClient(
        #     'mongodb://'+ HOST+':'+PORT+'/'+DATABASE)
        # self.client = MongoClient('mongodb://localhost:27017')
        # self.client.admin.authenticate('admin', 'CIST#2o!7', mechanism='SCRAM-SHA-256')
        # self.client = MongoClient(['10.0.8.32'], port=9042)
        self.database = 'articles'

    def process_item(self, item, spider):
        database = self.client[self.database]
        driver.insert_article(database, item)
        return item
