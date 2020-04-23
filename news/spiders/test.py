import scrapy
import json


def remove_ctrl(string):
    string = string.replace('\n', '')
    string = string.replace('\0', '')
    string = string.replace('\t', '')
    string = string.replace('\r', '')
    return string


class DantriSpider(scrapy.Spider):
    name = 'test'
    start_urls = [
        "https://www.nguoiduatin.vn/video-sieu-truc-thang-tang-hinh-niem-tu-hao-the-he-moi-cua-quan-doi-my-a452983.html"]

    def start_requests(self):
        return [scrapy.Request("https://comment.vietid.net/comments?app_key=d9c694bd04eb35d96f1d71a84141d075&content_url=http://kenh14.vn/news-20191021231634269.chn&news_title=Q8OzIG3hu5dpIGNodXnhu4duICJtdWEgbcOobyDhu58gxJHDonUiIGPFqW5nIGfDonkgYsOjbyBNWEg%2fIOG7pmEgbeG7h3Qga2jDtG5nPyBN4buHdCB0aMOsIGNvaSBj4bqpbSBuYW5nIMSR4buDIGjhu49pIHBow6F0IMSDbiBsdcO0biBuw6gh&num_count=5&debugcache=1&min=0&scroll=0&http_referer=http://kenh14.vn/co-moi-chuyen-mua-meo-o-dau-cung-gay-bao-mxh-ua-met-khong-met-thi-coi-cam-nang-de-hoi-phat-an-luon-ne-20191021231634269.chn&verify=1&verify_flag=6dd71280c421ba5589a03a05e7e07410&funny_flag=0&height=238&iframe_comment_id=mingid_comment_iframe&comment_flag=0&news_url_short=doi-song&real_time=undefined&is_hidden_comment=0", callback=self.parse_comment)]

    def parse(self, response):
        article = {}

        id_finder = response.xpath(
            '//script[@type="text/javascript"]/@src').get()
        id = id_finder.replace('//embed.easyvideo.vn/play', '')
        video_finder = "https://embed.easyvideo.vn/render/" + \
            id+"?targetId=MeCloudLoader_"+id
        yield scrapy.Request(video_finder, callback=self.parse_video, meta={'article': article})

    def parse_video(self, response):
        string = ''
        for a in response.xpath('//text()').getall():
            string += a
        pv1 = string.find('720p')
        if pv1 < 0:
            pv1 = string.find('480p')
            if pv1 < 0:
                pv1 = string.find('360p')
        pv2 = pv1 + string[pv1:].find(':') + 1
        pv3 = pv2 + string[pv2:].find('?')
        video_url = string[pv2:pv3]

        log = response.meta['article']
        log.update({'video-urls': video_url})
        yield log

    def get_comment(self, response, XPATH, counter):
        comments = []
        for comment in response.xpath(XPATH):
            comment_dict = {}
            primary_comment = comment.xpath('./div[contains(@id,"form")]')
            primary_ava = primary_comment.xpath(
                './/div[@class="avatar"]//img/@src').get()
            primary_user = primary_comment.xpath(
                './/a[@class="full-name"]/text()').get().strip()
            primary_time = primary_comment.xpath(
                '//span[@class="time-ago"]/text()').get().strip()
            primary_geo = primary_comment.xpath(
                './/span[@class="city"]/text()').get().strip()
            primary_content = primary_comment.xpath(
                './/div[@class="cm-content"]/span/text()').get().strip()
            primary_likes = primary_comment.xpath(
                './/a[contains(@class,"vote-count")]/text()').get().strip()

            comment_dict.update({
                'SenderAvatar': primary_ava,
                'SenderFullName': primary_user,
                'Publishedtime': primary_time,
                'PublishedGeo': primary_geo,
                'CommentContent': primary_content,
                'Liked': primary_likes,
            })
            counter += 1
            if response.xpath('.//ul[@class="sub-cm "]') is None:
                comment_dict.update({'Replies-count': 0,
                                     'Replies': None})
                comments.append(comment_dict)
            else:
                [secondary_dict, secondary_count] = self.get_comment(
                    comment, './/ul[@class="sub-cm "]/li', 0)
                comment_dict.update({'Replies-count': secondary_count,
                                     'Replies': secondary_dict})
            comments.append(comment_dict)
        return [comments, counter]

    def parse_comment(self, response):

        yield {'comments': comments}
