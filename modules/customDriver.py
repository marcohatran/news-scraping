from datetime import datetime
import json
import uuid


def timestamp_converter(ld_dict):
    date_published = ld_dict.get('datePublished')
    date_modified = ld_dict.get('dateModified')
    oldFormat = "%m/%d/%Y %I:%M:%S %p"
    newFormat = "%Y-%m-%d %H:%M:%S"

    date_published = datetime.strptime(date_published, oldFormat)
    Date_published = date_published.strftime(newFormat)

    date_modified = datetime.strptime(date_modified, oldFormat)
    Date_modified = date_modified.strftime(newFormat)

    ld_dict['datePublished'] = Date_published
    ld_dict['dateModified'] = Date_modified

    return ld_dict


def get_comments_list(comment, article_id, parent_cmt_id):
    comment_list = []
    comment_id = uuid.uuid1()
    author = comment.get('SenderFullName')
    content = comment.get('CommentContent')
    created_at = comment.get('CreatedDate')
    like = int(comment.get('Liked'))

    db_comment = {
        'comment_id': comment_id,
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

    if comment['Replies'] is not None:
        for reply in comment['Replies']:
            comment_list.extend(self.get_comments_list(
                reply, article_id, comment_id))

    return comment_list


def insert_article(session, article):
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

    type = article.get('@type')
    if type is None:
        type = '-1'

    date_published = article.get('datePublished')
    if date_published is None:
        date_published = '-1'

    date_modified = article.get('dateModified')
    if date_modified is None:
        date_modified = '-1'

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

    content = article.get('content')
    if content is None:
        content = '-1'

    images = json.dumps(article.get('image-urls'))
    if images is None:
        images = '-1'

    keywords = article.get('meta-keywords')
    if keywords is None:
        keywords = '-1'

    category = article.get('category')
    if category is None:
        category = '-1'

    language = article.get('language')
    if language is None:
        language = '-1'

    geo_placename = article.get('geo.placename')
    if geo_placename is None:
        geo_placename = '-1'

    geo_region = article.get('geo.region')
    if geo_region is None:
        geo_region = '-1'

    geo_position = article.get('geo.position')
    if geo_position is None:
        geo_position = '-1'

    word_count = article.get('word_count')
    if word_count is None:
        word_count = -1

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
        'language': language,
        'geo.placename': geo_placename,
        'geo.region': geo_region,
        'geo.position': geo_position,
        'word_count': word_count,
        'url': url,
        'like': like,
        'share': share,
        'seen': seen,
        'relate_urls': related_urls,
        'raw_data': raw_data
    }

    article_id = uuid.uuid1()

    search_for_article = session.execute(
        """
        SELECT * FROM articles WHERE url = '%s'
            """ % url
    )

    if len(search_for_article.current_rows) is 0:
        searched_article_id = article_id
    else:
        searched_article_id = search_for_article.current_rows[0].article_id

    session.execute(
        """
            UPDATE articles SET headline = %s, thumbnail = %s, description = %s, type = %s, date_published = %s, date_modified = %s,
            author = %s, publisher = %s, content = %s, images = %s, keywords = %s, category = %s, language = %s, geo_place_name = %s, geo_region = %s,
            geo_position = %s, word_count= %s, url = %s, like = %s, share = %s, seen = %s, related_urls = %s, raw_data = %s
            WHERE article_id = %s 
            """,
        tuple(db_article.values()) +
        (searched_article_id,)
    )

    Comments = article.get('comments')
    if Comments is not None and len(Comments) != 0:
        for comment in Comments:
            comment_and_replies = get_comments_list(
                comment, searched_article_id, None)
            for comment_insert in comment_and_replies:

                search_for_comment = session.execute(
                    """
                    SELECT * FROM article_comments WHERE article_id = %s AND content = %s 
                        """,
                    (searched_article_id,
                        comment_insert.get('content'))
                )

                if len(search_for_comment.current_rows) is 0:
                    searched_comment_id = comment_insert['comment_id']
                else:
                    searched_comment_id = search_for_comment.current_rows[0].comment_id

                del comment_insert['comment_id']
                session.execute(
                    """
                        UPDATE article_comments SET article_id = %s, author = %s, content = %s, created_at = %s, like = %s, commentreplyid = %s WHERE comment_id = %s 
                        """, tuple(comment_insert.values()) + (searched_comment_id, )
                )
