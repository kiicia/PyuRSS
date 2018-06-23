import urllib.request as REQ
import xml.dom.minidom as MDOM
import datetime as DT
import sqlite3

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

def check(feeds):
    connection = sqlite3.connect('feeds.db')
    cursor = connection.cursor()
    cursor.execute('''create table if not exists articles (
id integer primary key,
guid text unique not null,
published date,
title text,
link text,
article text,
read integer,
feed integer not null,
foreign key(feed) references feeds(id)
)''')
    print('feeds',len(feeds))
    for f in feeds:
        print('checking',f[1]);
        for a in feed(f[2]):
            exists = cursor.execute('''select 1 from articles
where guid = ?''', [a[0]]).fetchone()
            print('inserting?', not exists, a[2])
            if not exists:
                a = a + (f[0], 0)
                cursor.execute('''insert into articles
(guid, published, title, link, read, feed) values (?, ?, ?, ?, ?, ?)''', a)
        cursor.execute('''update feeds set lastChecked = ? where id = ?''', [DT.datetime.now(), f[0]])
    connection.commit()
    connection.close()

def insertTestFeeds(cursor):
    f = [
        ('BleepingComputer','https://www.bleepingcomputer.com/feed/'),
        ('The Verge','https://www.theverge.com/rss/front-page/index.xml')
        ]
    cursor.executemany('insert into feeds (name, link) values (?, ?)', f)

def checkDb():
    connection = sqlite3.connect('feeds.db')
    cursor = connection.cursor()
    for f in cursor.execute('select * from feeds'):
        print(f)
    for r in cursor.execute('select * from articles'):
        print(r)

def listFeeds():
    connection = sqlite3.connect('feeds.db')
    cursor = connection.cursor()
    cursor.execute('''create table if not exists feeds (
id integer primary key,
name text,
link text unique not null,
lastChecked date
)''')
    #insertTestFeeds(cursor)
    feeds = cursor.execute('select * from feeds').fetchall()
    connection.commit()
    connection.close()
    return feeds

check(listFeeds())
checkDb()
