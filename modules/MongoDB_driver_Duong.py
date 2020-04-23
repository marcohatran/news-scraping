import json
from bson.objectid import ObjectId

def check(string, dict):
    try:
        return dict[string]
    except KeyError:
        return "-1"

def checknumber(string, dict):
    try:
        return dict[string]
    except KeyError:
        return -1

# lấy các comment trong báo
def list_comment(cmt, article_id, cmt_id_goc):
    data_comment = dict()
    list_all_comment = []
    comment_id = ObjectId()
    content_cmt = cmt["content"]
    author = cmt["sender_fullname"]
    like = int(cmt["likes"])
    created_at = cmt["created_date"]
    data_comment.update(
        {'comment_id': comment_id, 'article_id': article_id, 'content': content_cmt, "author": author, "like": like, "created_at": created_at})
    if cmt_id_goc is not None:
        data_comment.update({'commentreplyid': cmt_id_goc})
    else:
        data_comment.update({'commentreplyid': None})
    list_all_comment.append(data_comment)
    if cmt['child_comments'] is not None:
        for cmt_reply in cmt['child_comments']:
            reply = list_comment(cmt_reply, article_id, comment_id)
            list_all_comment.extend(reply)
    return list_all_comment

def list_comment_vne(cmt, article_id, cmt_id_goc):
    data_comment = dict()
    list_all_comment = []
    comment_id = ObjectId()
    content_cmt = cmt.get('content')
    author = cmt.get('full_name')
    like = cmt.get("userlike")
    data_comment.update(
        {'comment_id': comment_id, 'article_id': article_id, 'content': content_cmt, "author": author, "like": like})
    if cmt_id_goc is not None:
        data_comment.update({'commentreplyid': cmt_id_goc})
    else:
        data_comment.update({'commentreplyid': None})
    list_all_comment.append(data_comment)

    if cmt.get('replys') is not None:
        a = cmt.get('replys')
        if a.get('items') is not None:
            for i in a.get('items'):
                reply = list_comment_vne(i, article_id, comment_id)
                list_all_comment.extend(reply)
    return list_all_comment

# insert và update dữ liệu lên db
def insert_data_article(db, article):
    # insert article
    data_article = dict()
    headline = check("headline", article)
    thumbnail = str(check("thumbnail", article))
    description = check("description", article)
    type_article = check("type", article)
    date_published = check("datePublished", article)
    date_modified = check("dateModified", article)
    author = check("author", article)
    publishers = check("publisher", article)
    publisher = json.dumps(publishers)
    content = check("content_article", article)
    images1 = check("image", article)
    images = json.dumps(images1)
    keywords = check("keywords", article)
    category = check("category", article)
    language = check("language", article)
    geo_place_name = check("geo_place_name", article)
    geo_region = check("geo_region", article)
    geo_position = check("geo_position", article)
    word_count = checknumber("word_count", article)
    url = check("link", article)
    like = int(checknumber("like_count", article))
    share = int(checknumber("share_count", article))
    seen = int(checknumber("seen", article))
    related_urls1 = check("related_url", article)
    related_urls = json.dumps(related_urls1)
    organization = check("organization", article)
    raw_data = "-1"
    data_article.update(
        {
            'headline': headline, 'thumbnail': thumbnail, 'description': description, 'type': type_article,
            'date_published': date_published, 'date_modified': date_modified, 'author': author, 'publisher': publisher,
            'content': content, 'images': images, 'keywords': keywords, 'category': category, 'language': language,
            'geo_place_name': geo_place_name, 'geo_region': geo_region, 'geo_position': geo_position,
            'word_count': word_count, 'url': url, 'like': like, 'share': share, 'seen': seen, 'organization': organization,
            'related_urls': related_urls

        })
    Article = dict()
    search_for_article = db['articles'].find_one({'url': url})
    if search_for_article is None:
        searched_article_id = ObjectId()
        Article = {'_id': searched_article_id}
        Article.update(data_article)
        db['articles'].insert_one(Article)
    else:
        searched_article_id = search_for_article.get('_id')
        db['articles'].update_one(search_for_article,
                                  {'$set': data_article}, True)
    try:
        json_comment = article["comment_article"]
        if 'data_vn' in json_comment:
            inf_comment = json_comment['data_vn']
            comments = inf_comment
            for cmt in comments:
                all_comment = list_comment_vne(cmt, searched_article_id, None)
                for comment_insert in all_comment:
                    search_for_comment = db['comments'].find_one(
                        {
                            'article_id': searched_article_id,
                            'content': comment_insert.get('content')
                        }
                    )
                    if search_for_comment is None:
                        db['comments'].insert_one(comment_insert)
                    else:
                        db['comments'].update_one(search_for_comment, {'$set': comment_insert}, True)
        elif 'Data' in json_comment:
            inf_comment = json_comment['Data']
            comments = json.loads(inf_comment)
            for cmt in comments:
                all_comment = list_comment(cmt, searched_article_id, None)
                for comment_insert in all_comment:
                    search_for_comment = db['comments'].find_one(
                        {
                            'article_id': searched_article_id,
                            'content': comment_insert.get('content')
                        }
                    )
                    if search_for_comment is None:
                        db['comments'].insert_one(comment_insert)
                    else:
                        db['comments'].update_one(search_for_comment, {'$set': comment_insert}, True)
        else:
            pass
    except:
        pass