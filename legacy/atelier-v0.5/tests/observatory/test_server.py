"""Loopback server exposes no arbitrary files, commands, or cross-origin feed."""
import http.client,importlib.util,threading,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('observatoryServer',ROOT/'scripts/serve_observatory.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ServerTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.server=m.http.server.ThreadingHTTPServer(('127.0.0.1',0),m.Handler);cls.server.daemon_threads=True;cls.port=cls.server.server_port;cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
 @classmethod
 def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.thread.join(2)
 def request(self,path='/',headers=None):
  c=http.client.HTTPConnection('127.0.0.1',self.port,timeout=2);c.request('GET',path,headers=headers or {});r=c.getresponse();status=r.status;data=r.read() if path!='/events' or status!=200 else r.readline();c.close();return status,data,dict(r.getheaders())
 def test_exact_gallery(self):
  status,data,h=self.request();self.assertEqual(status,200);self.assertEqual(data,(ROOT/'Nocturne-Observatory.html').read_bytes());self.assertIn("frame-ancestors 'none'",h['Content-Security-Policy'])
 def test_no_arbitrary_files(self):self.assertEqual(self.request('/../../etc/passwd')[0],404)
 def test_cross_origin_rejected(self):self.assertEqual(self.request('/events',{'Origin':'https://untrusted.example'})[0],403)
 def test_rebinding_host_rejected(self):self.assertEqual(self.request('/',{'Host':'untrusted.example'})[0],403)
 def test_fetch_metadata_rejected(self):self.assertEqual(self.request('/events',{'Sec-Fetch-Site':'cross-site'})[0],403)
if __name__=='__main__':unittest.main()
