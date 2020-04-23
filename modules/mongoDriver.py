import json
from bson.objectid import ObjectId


def checkExist(dataType, article):
    try:
        return article.get(dataType)
    except KeyError:
        return '-1'


def get_comments_list(comment, article_id, parent_cmt_id):
    comment_list = []
    author = comment.get('SenderFullName')
    content = comment.get('CommentContent')
    created_at = comment.get('CreatedDate')

    try:
        created_at = float(created_at)
    except:
        pass

    if comment.get('Liked') is not None:
        like = int(comment.get('Liked'))
    elif comment.get('Like') is not None:
        like = int(comment.get('Like'))
    else:
        like = -1

    comment_id = ObjectId()

    db_comment = {
        '_id': comment_id,
        'article_id': article_id,
        'author': author,
        'content': content,
        'created_at': created_at,
        'like': like
    }
    if parent_cmt_id is not None:
        db_comment.update({'commentreplyid': parent_cmt_id})
    else:
        db_comment.update({'commentreplyid': None})
    comment_list.append(db_comment)

    if comment.get('Replies') is not None:
        for reply in comment['Replies']:
            comment_list.extend(get_comments_list(
                reply, article_id, comment_id))

    return comment_list


def insert_article(database, article, name):
    headline = article.get('headline')
    if headline is None:
        headline = article.get('meta-title')
        if headline is None:
            headline = '-1'

    thumbnail = json.dumps(article.get('image'))
    if thumbnail is None:
        thumbnail = '-1'

    description = article.get('description')
    if description is None:
        description = article.get('meta-description')
        if description is None:
            description = '-1'

    type = checkExist('@type', article)
    date_published = checkExist('datePublished', article)
    date_modified = checkExist('dateModified', article)
    author = json.dumps(article.get('author'))
    if author is None:
        author = article.get('meta-article:author')
        if author is None:
            author = '-1'
    publisher = json.dumps(article.get('publisher'))
    if publisher is None:
        publisher = article.get('meta-article:publisher')
        if publisher is None:
            publisher = '-1'
    content = checkExist('content', article)

    images = json.dumps(article.get('image-urls'))
    if images is None:
        images = '-1'

    keywords = checkExist('meta-keywords', article)
    category = checkExist('category', article)
    organization = checkExist('organization', article)

    language = checkExist('language', article)
    geo_placename = checkExist('geo.placename', article)
    geo_region = checkExist('geo.region', article)
    geo_position = checkExist('geo.position', article)
    word_count = checkExist('word_count', article)
    url = article.get('url')

    interactions = article.get('interactions')
    like = article.get('likes-counter')
    if like is None:
        like = article.get('like_count')
        if like is None:
            if interactions is not None:
                like = interactions.get('like_count')
            if like is None:
                like = "-1"
    if "k" in like.lower():
        like = like.lower()
        like = like.replace(",", ".")
        like = like.replace("k", "")
        like = float(like) * 1000
    like = int(like)

    share = article.get('share_count')
    if share is None:
        if interactions is not None:
            share = interactions.get('share_count')
        if share is None:
            share = '-1'
    if "k" in share.lower():
        share = share.lower()
        share = share.replace(",", ".")
        share = share.replace("k", "")
        share = float(share) * 1000
    share = int(share)

    seen = article.get('view-count')
    if seen is None:
        seen = article.get('views')
        if seen is None:
            seen = '-1'

    if "k" in seen.lower():
        seen = seen.lower()
        seen = seen.replace(",", ".")
        seen = seen.replace("k", "")
        seen = float(seen) * 1000
    seen = int(seen)

    related_urls = json.dumps(article.get('related_urls'))
    if related_urls is None:
        related_urls = "-1"

    raw_data = '-1'

    db_article = {
        'headline': headline,
        'thumbnail': thumbnail,
        'description': description,
        'type': type,
        'date_published': date_published,
        'date_modified': date_modified,
        'author': author,
        'publisher': publisher,
        'content': content,
        'images': images,
        'keywords': keywords,
        'category': category,
        'organization': organization,
        'language': language,
        'geo_placename': geo_placename,
        'geo_region': geo_region,
        'geo_position': geo_position,
        'word_count': word_count,
        'url': url,
        'like': like,
        'share': share,
        'seen': seen,
        'relate_urls': related_urls,
        'raw_data': raw_data
    }

    collection = database[name]

    search_for_article = collection.find_one(
        {
            'url': url
        }
    )

    if search_for_article is None:
        searched_article_id = ObjectId()
        Article = {'_id': searched_article_id}
        Article.update(db_article)

        collection.insert_one(Article)

    else:
        searched_article_id = search_for_article.get('_id')
        collection.update_one(search_for_article,
                              {'$set': db_article}, True)

    Comments = article.get('comments')
    if Comments is not None and len(Comments) != 0:
        for comment in Comments:
            comment_and_replies = get_comments_list(
                comment, searched_article_id, None)
            for comment_insert in comment_and_replies:
                cmt_collection = database[name+'_comments']

                search_for_comment = cmt_collection.find_one(
                    {
                        'article_id': searched_article_id,
                        'content': comment_insert.get('content')
                    }
                )

                if search_for_comment is None:
                    cmt_collection.insert_one(
                        comment_insert
                    )
                else:
                    del comment_insert['_id']
                    del comment_insert['commentreplyid']

                    cmt_collection.update_one(
                        search_for_comment,  {'$set': comment_insert}, True)
