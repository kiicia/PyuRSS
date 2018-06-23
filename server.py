from http.server import HTTPServer, BaseHTTPRequestHandler
import re

_404 = '''<p>404 :(<br/><a href="/">goto /</a></p>'''

head = '''<html>
<head>
<title>PyuRSS</title>
<style>
a {
    color: black;
    text-decoration: underline;
}
</style>
</head>
<body>'''

tail = '''</body>
</html>'''

def response(self,text):
    self.wfile.write(text.encode('utf-8'))

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

def do_open_html(function):
    def wrapper(self):
        response(self,head)
        function(self)
    return wrapper

def do_close_html(function):
    def wrapper(self):
        response(self,tail)
        function(self)
    return wrapper

class FeedRequestHandler(BaseHTTPRequestHandler):
    @do_respond_200_html
    @do_open_html
    @do_handle('^/?$',lambda self, m: response(self,'listing feeds'))
    @do_handle('^/add/?$',lambda self, m: response(self,'adding feed'))
    @do_handle('^/f/(\d+)/?$',lambda self, m: response(self,
        'listing articles of #{}'.format(m.group(1))))
    @do_handle('^/a/(\d+)/?$',lambda self, m: response(self,
        'article #{}'.format(m.group(1))))
    @do_close_html
    def do_GET(self):
        response(self,_404)

def run_server(server_class=HTTPServer, handler_class=BaseHTTPRequestHandler):
    server_address = ('', 8000)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()

run_server(handler_class=FeedRequestHandler)
