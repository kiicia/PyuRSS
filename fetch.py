import urllib.request as REQ
import xml.dom.minidom as MDOM
import datetime as DT
import sqlite3

sql_create_articles = '''
create table if not exists articles (
id integer primary key,
guid text unique not null,
published date,
title text,
link text,
article text,
read integer,
feed integer not null,
foreign key(feed) references feeds(id)
)
'''

sql_insert_article = '''
insert into articles (guid, published, title, link, read, feed) values (?, ?, ?, ?, ?, ?)
'''

sql_exists_article = '''
select 1 from articles where guid = ?
'''

sql_list_articles = '''
select id, title from articles where feed = ? order by id desc limit 100
'''

sql_get_article = '''
select * from articles where id = ?
'''

sql_create_feeds = '''
create table if not exists feeds (
id integer primary key,
name text,
link text unique not null,
lastChecked date
)
'''

sql_insert_feed = '''
insert into feeds (name, link) values (?, ?)
'''

sql_update_feed_checked = '''
update feeds set lastChecked = ? where id = ?
'''

sql_list_feeds = '''
select * from feeds
'''

sql_get_feed = '''
select * from feeds where id = ?
'''

db_name = 'feeds.db'

def db_access(function):
    def wrapper(*args, **kwargs):
        connection = sqlite3.connect(db_name)
        cursor = connection.cursor()
        kwargs['cursor'] = cursor
        returned = function(*args, **kwargs)
        connection.commit()
        connection.close()
        return returned
    return wrapper

def fetch(url):
    response = REQ.urlopen(url)
    status = response.getcode()
    if status == 200:
        return response.read().decode('UTF-8')
    else:
        raise Exception(status, url)

def tagValue(node, name):
    found = node.getElementsByTagName(name)
    if found and len(found) > 0:
        return found[0].firstChild.nodeValue
    
def tagAttr(node, name, attr):
    found = node.getElementsByTagName(name)
    if found and len(found) > 0:
        return found[0].getAttribute(attr)

def parseFeed(dom, itemT, guidT, titleT, linkT, linkA, dateT, dateL, dateF):
    items = []
    for item in dom.getElementsByTagName(itemT):
        guid = tagValue(item, guidT)
        title = tagValue(item, titleT)
        if linkA:
            link = tagAttr(item, linkT, linkA)
        else:
            link = tagValue(item, linkT)
        pubDate = tagValue(item, dateT)
        date = DT.datetime.strptime(dateL(pubDate), dateF)
        items.append((guid, date, title, link))
    return items

def rss(dom):
    pre = lambda d: d[:d.rindex(' ')]
    fmt = '%a, %d %b %Y %H:%M:%S'
    return parseFeed(dom, 'item', 'guid', 'title', 'link', None, 'pubDate', pre, fmt)

def atom(dom):
    pre = lambda d: d[:d.rindex(':')] + d[d.rindex(':')+1:]
    fmt = '%Y-%m-%dT%H:%M:%S%z'
    return parseFeed(dom, 'entry', 'id', 'title', 'link', 'href', 'published', pre, fmt)

def feed(url):
    txt = fetch(url)
    dom = MDOM.parseString(txt)
    root = dom.firstChild.tagName
    if root == 'rss':
        return rss(dom)
    elif root == 'feed':
        return atom(dom)
    else:
        raise Exception('Unknown feed type', root)

@db_access
def check(feeds, cursor=None):
    cursor.execute(sql_create_articles)
    print('feeds',len(feeds))
    for f in feeds:
        print('checking',f[1]);
        for a in feed(f[2]):
            exists = cursor.execute(sql_exists_article, [a[0]]).fetchone()
            print('inserting?', not exists, a[2])
            if not exists:
                a = a + (0, f[0])
                cursor.execute(sql_insert_article, a)
        cursor.execute(sql_update_feed_checked, [DT.datetime.now(), f[0]])

def insertTestFeeds(cursor):
    f = [
        ('BleepingComputer','https://www.bleepingcomputer.com/feed/'),
        ('The Verge','https://www.theverge.com/rss/front-page/index.xml')
        ]
    cursor.executemany(sql_insert_feed, f)

@db_access
def checkDb(cursor):
    #for f in cursor.execute('select * from feeds'):
        #print(f)
    #for r in cursor.execute('select * from articles'):
        #print(r)
    for x in cursor.execute(sql_list_articles,(1,)):
        print(x)

@db_access
def listFeeds(cursor=None):
    cursor.execute(sql_create_feeds)
    return cursor.execute(sql_list_feeds).fetchall()

@db_access
def getFeed(feed,cursor=None):
    cursor.execute(sql_create_feeds)
    return cursor.execute(sql_get_feed,(feed,)).fetchone()

@db_access
def listArticles(feed,cursor=None):
    cursor.execute(sql_create_articles)
    return cursor.execute(sql_list_articles,(feed,)).fetchall()

@db_access
def getArticle(article,cursor=None):
    cursor.execute(sql_create_articles)
    return cursor.execute(sql_get_article,(article,)).fetchone()

@db_access
def add_feed(name, url, cursor=None):
    cursor.execute(sql_create_feeds)
    cursor.execute(sql_insert_feed, (name, url))

#check(listFeeds())
#checkDb()
