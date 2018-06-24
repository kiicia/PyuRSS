from http.server import HTTPServer, BaseHTTPRequestHandler
import re
from urllib.parse import unquote
import fetch as RSS

#import hashlib
#hashlib.sha256('password'.encode('utf-8')).hexdigest()

def load_html(name):
    file = open(name,'r')
    html = file.read()
    file.close()
    return html

def response(self,text):
    self.wfile.write(text.encode('utf-8'))

def decodeuri(text):
    return unquote(text.replace('+',' '))

def form_data(data):
    d = {}
    for f in data.split('&'):
        ff = f.split('=')
        d[decodeuri(ff[0])] = decodeuri(ff[1])
    return d

def read_form(self):
    length = self.headers['content-length']
    data = self.rfile.read(int(length)).decode()
    return form_data(data)

def do_handle(pattern,action):
    def decorator(function):
        def wrapper(self):
            m = re.search(pattern,self.path)
            if m:
                action(self,m)
            else:
                function(self)
        return wrapper
    return decorator

def do_respond_200_html(function):
    def wrapper(self):
        print('handling',self.path)
        self.send_response(200)
        self.send_header('Content-type','text/html; charset=utf-8')
        self.end_headers()
        function(self)
    return wrapper

def do_create_html(function):
    def wrapper(self):
        parts = load_html('body.html').split('{}')
        response(self,parts[0])
        function(self)
        response(self,parts[1])
    return wrapper

def do_update(self,m):
    feeds = RSS.listFeeds()
    l = len(feeds)
    for i,feed in enumerate(feeds):
        response(self,'updating ({}/{}) {}...<br/>'.format(i+1,l,feed[1]))
        RSS.check([feed])
    response(self,'update done <a href="/">goto /</a>')

def add_feed_form(self,m):
    response(self,load_html('add_form.html'))

def add_feed_action(self,m):
    form = read_form(self)
    print('adding {}'.format(form))
    RSS.add_feed(form['name'], form['url'])
    response(self,'<p>added: {}<br><a href="/">goto /</a></p>'.format(form))

def list_feeds(self,m):
    parts = load_html('main.html').split('{}')
    response(self,parts[0])
    feeds = RSS.listFeeds()
    for feed in feeds:
        url, name = '/f/{}'.format(feed[0]), feed[1]
        response(self,'<a href="{}">{}</a><br/>'.format(url,name))
    response(self,parts[1])

def list_articles(self,m):
    parts = load_html('feed.html').split('{}')
    feed = RSS.getFeed(m.group(1))
    print('listing articles for',feed)
    articles = RSS.listArticles(feed[0])
    response(self,parts[0].format(feed[1]))
    for article in articles:
        url, name = '/a/{}'.format(article[0]), article[1]
        response(self,'<a href="{}">{}</a><br/>'.format(url,name))
    response(self,parts[1])

def show_article(self,m):
    parts = load_html('article.html').split('{}')
    article = RSS.getArticle(m.group(1))
    feed = RSS.getFeed(article[7])
    response(self,parts[0].format(article[3],feed[1],article[2]))
    response(self,article[5] if article[5] else '')
    response(self,parts[1])

class FeedRequestHandler(BaseHTTPRequestHandler):
    
    @do_respond_200_html
    @do_create_html
    @do_handle('^/?$',list_feeds)
    @do_handle('^/add/?$',add_feed_form)
    @do_handle('^/f/(\d+)/?$',list_articles)
    @do_handle('^/a/(\d+)/?$',show_article)
    @do_handle('^/update/?$',do_update)
    def do_GET(self):
        response(self,load_html('404.html'))

    @do_respond_200_html
    @do_create_html
    @do_handle('^/add/?$',add_feed_action)
    def do_POST(self):
        response(self,load_html('404.html'))

def run_server(server_class=HTTPServer, handler_class=BaseHTTPRequestHandler):
    server_address = ('', 8000)
    httpd = server_class(server_address, handler_class)
    print('rss server started')
    httpd.serve_forever()
    print('rss server halted')

run_server(handler_class=FeedRequestHandler)
