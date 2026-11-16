#!/usr/bin/env python3
"""Serve only the gallery and an explicit same-origin sensor stream on loopback.

No filesystem browser, uploads, command execution, CORS, or automatic capture.
Open http://127.0.0.1:8765 and click Connect localhost sensors to subscribe.
"""
from __future__ import annotations
import argparse,http.server,importlib.util,json,threading,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('sampler',ROOT/'sensors/system_sensors.py');samplerModule=importlib.util.module_from_spec(spec);spec.loader.exec_module(samplerModule)
SLOTS=threading.BoundedSemaphore(4)
class Handler(http.server.BaseHTTPRequestHandler):
    server_version='NocturneReadOnly/0.4'
    def log_message(self,*args):pass
    def do_GET(self):
        port=self.server.server_port;host=self.headers.get('Host','');allowed={f'127.0.0.1:{port}',f'localhost:{port}'}
        origin=self.headers.get('Origin');site=self.headers.get('Sec-Fetch-Site','')
        if host not in allowed or (origin and origin not in {'http://'+v for v in allowed}) or site=='cross-site':self.send_error(403,'Loopback same-origin requests only');return
        path=self.path.split('?',1)[0]
        if path in ('/','/Nocturne-Observatory.html'):
            data=(ROOT/'Nocturne-Observatory.html').read_bytes();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Security-Policy',"default-src 'self' data: blob:; script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval'; style-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'none'");self.end_headers();self.wfile.write(data);return
        if path!='/events':self.send_error(404);return
        if not SLOTS.acquire(blocking=False):self.send_error(503,'Four sensor subscriptions maximum');return
        try:
            self.send_response(200);self.send_header('Content-Type','text/event-stream');self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();sampler=samplerModule.SystemSampler()
            while True:
                rows=sampler.poll(time.monotonic_ns()/1e6)
                if rows:
                    for row in rows:self.wfile.write(('data: '+json.dumps(row,separators=(',',':'))+'\n\n').encode())
                else:self.wfile.write(b': no accessible sensor samples yet\n\n')
                self.wfile.flush();time.sleep(.25)
        except (BrokenPipeError,ConnectionResetError):pass
        finally:SLOTS.release()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--port',type=int,default=8765);a=p.parse_args()
    if not 1024<=a.port<=65535:p.error('port 1024..65535 required')
    server=http.server.ThreadingHTTPServer(('127.0.0.1',a.port),Handler);server.daemon_threads=True
    print(f'Nocturne: http://127.0.0.1:{a.port} · read-only · Ctrl+C stops',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
if __name__=='__main__':main()
