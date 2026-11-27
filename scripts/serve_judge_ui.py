#!/usr/bin/env python3
"""Local-only VerdictKit read-only UI bridge. Never exposes a public listener."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import http.client
import json
import socket
from urllib.parse import urlsplit

MAX_RESPONSE = 8 * 1024 * 1024
# BE-2 root cause: a refused loopback connect takes about 2.05 s on Windows (the stack retries the
# SYN after the reset; 7 of 7 trials on any port) but is instant on Linux. One 10 s timeout covered
# connect and read alike, so a dead backend was reported after the caller had already given up.
# The upstream is always loopback, where a live listener accepts in microseconds, so the connect
# phase gets its own short bound. Reads keep their long one.
CONNECT_TIMEOUT_S = 1.0
READ_TIMEOUT_S = 10.0


class LoopbackConnection(http.client.HTTPConnection):
    def connect(self):
        self.sock = socket.create_connection((self.host, self.port), timeout=CONNECT_TIMEOUT_S)
        self.sock.settimeout(READ_TIMEOUT_S)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)


UI = Path(__file__).resolve().parent.parent / 'ui' / 'judge'
MIMES = {'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8'}

class Handler(BaseHTTPRequestHandler):
    server_version = 'VerdictKitJudgePreview/1.0'
    def do_GET(self):
        path = urlsplit(self.path).path
        if path in ('/', '/index.html', '/style.css', '/app.js'):
            target = 'index.html' if path == '/' else path.lstrip('/')
            file = UI / target
            if not file.is_file():
                return self.send_error(404)
            data = file.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type',MIMES[file.suffix])
            self.send_header('Content-Length',str(len(data)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.end_headers();self.wfile.write(data)
            return
        if path.startswith('/api/v1/') and not urlsplit(self.path).query:
            # GET-only, allowlisted operations. Does not forward credentials or browser headers.
            import re
            allowed = (path == '/api/v1/health' or path == '/api/v1/claim-types'
                or re.fullmatch(r'/api/v1/cases/[A-Za-z0-9_-]{8,100}/(?:outcome|bundle(?:/metadata)?)',path))
            if not allowed:
                return self.send_error(403,'Route not permitted in preview bridge')
            try:
                conn = LoopbackConnection('127.0.0.1',self.server.api_port)
                conn.request('GET',path,headers={'Accept':'application/json, application/octet-stream'})
                upstream=conn.getresponse()
                length=upstream.getheader('Content-Length')
                if length and int(length)>MAX_RESPONSE:
                    conn.close();return self.send_error(502,'Upstream too large')
                data=upstream.read(MAX_RESPONSE+1)
                if len(data)>MAX_RESPONSE:
                    conn.close();return self.send_error(502,'Upstream too large')
                self.send_response(upstream.status)
                for k in ('Content-Type','X-VerdictKit-Contract'):
                    v=upstream.getheader(k)
                    if v:self.send_header(k,v)
                self.send_header('Content-Length',str(len(data)))
                self.send_header('Cache-Control','no-store')
                self.send_header('X-Content-Type-Options','nosniff')
                self.end_headers();self.wfile.write(data);conn.close()
            except (OSError,ValueError,http.client.HTTPException):
                error=json.dumps({'error':{'code':'BACKEND_UNAVAILABLE','message':'API backend is unavailable'}}).encode()
                self.send_response(502);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(error)));self.end_headers();self.wfile.write(error)
            return
        self.send_error(404)
    def do_POST(self):self.send_error(405,'Read-only preview')
    def do_PATCH(self):self.send_error(405,'Read-only preview')
    def do_PUT(self):self.send_error(405,'Read-only preview')
    def do_DELETE(self):self.send_error(405,'Read-only preview')
    def log_message(self,fmt,*args):pass # Avoid logging sensitive case identifiers.

def main():
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8766);p.add_argument('--api-port',type=int,default=8000)
    opts=p.parse_args()
    for val in (opts.port,opts.api_port):
        if not (1024<=val<=65535):p.error('ports must be 1024..65535')
    server=ThreadingHTTPServer(('127.0.0.1',opts.port),Handler);server.api_port=opts.api_port
    print('VerdictKit UI: http://127.0.0.1:'+str(opts.port),flush=True)
    print('Backend target: http://127.0.0.1:'+str(opts.api_port)+' (GET-only)',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
if __name__=='__main__':main()
