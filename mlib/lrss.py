#!/bin/python


#   RSS library
#   (c) IS 2015


import feedparser

def lrss():
#    pass
    rss = 'http://www.blog.pythonlibrary.org/feed/'
    rss = 'http://hnonline.sk/rss/1'
    rss = 'http://www.f-motel.sk/denne_menu_export.php'
    rss = 'http://www.borovasihot.sk/rss-tyzden.xml'
    try:
        feed = feedparser.parse(rss)
        print('RSS Ver: {0} {1}'.format(feed.version, feed.updated))
#        for key in feed:
#            print(key,' -> ')
        for post in feed.entries:
#            for key in post:
#                print(key,' -> ')
            title = post.title
            summary = post.summary
            link = post.link
            published = post.published
            print('- {0} @ {1}'.format(title, published))
    except:
        pass
