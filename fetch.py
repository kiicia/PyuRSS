import urllib.request as REQ
import xml.dom.minidom as MDOM
import datetime as DT

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
        pubDate = dateL(pubDate)
        date = DT.datetime.strptime(pubDate, dateF)
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

print(feed('https://www.bleepingcomputer.com/feed/'))
print(feed('https://www.theverge.com/rss/front-page/index.xml'))
