import http.client
import importlib.util
from pathlib import Path
import threading
import types
import unittest

ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location('judge_server',ROOT/'scripts'/'serve_judge_ui.py')
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)

class JudgePreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv=mod.ThreadingHTTPServer(('127.0.0.1',0),mod.Handler)
        cls.srv.api_port=65534
        cls.thread=threading.Thread(target=cls.srv.serve_forever,daemon=True);cls.thread.start()
    @classmethod
    def tearDownClass(cls):cls.srv.shutdown();cls.srv.server_close();cls.thread.join(timeout=3)
    def query(self,method,path):
        c=http.client.HTTPConnection('127.0.0.1',self.srv.server_port,timeout=2)
        c.request(method,path);r=c.getresponse();out=(r.status,dict(r.getheaders()),r.read());c.close();return out
    def test_main_html(self):
        status,headers,body=self.query('GET','/')
        self.assertEqual(status,200);self.assertIn(b'Verdict &amp; Evidence',body)
    def test_js_and_css(self):
        for path in ('/app.js','/style.css'):
            self.assertEqual(self.query('GET',path)[0],200)
    def test_no_path_traversal(self):self.assertEqual(self.query('GET','/../README.md')[0],404)
    def test_writes_rejected(self):self.assertEqual(self.query('POST','/api/v1/cases')[0],405)
    def test_unknown_get_rejected(self):self.assertEqual(self.query('GET','/api/v1/cases')[0],403)
    def test_case_outcome_get_to_offline_backend(self):self.assertEqual(self.query('GET','/api/v1/cases/abcdef0123456789/outcome')[0],502)
    def test_upstream_connect_phase_has_its_own_bound_below_the_callers_patience(self):
        """BE-2 root cause: a refused loopback connect takes ~2 s on Windows, so the connect phase
        must be bounded separately from the read phase (checked here on every host)."""
        seen = []

        def refuse(address, timeout=None, **_kw):
            seen.append(timeout)
            raise ConnectionRefusedError()
        real = mod.socket
        mod.socket = types.SimpleNamespace(create_connection=refuse)   # only the bridge sees the stub
        try:
            self.assertEqual(self.query('GET','/api/v1/health')[0],502)
        finally:
            mod.socket = real
        self.assertEqual(seen,[mod.CONNECT_TIMEOUT_S])
        self.assertLess(mod.CONNECT_TIMEOUT_S,2.0,'the connect bound must be below the 2 s the preview client waits')
        self.assertGreater(mod.READ_TIMEOUT_S,mod.CONNECT_TIMEOUT_S)
    def test_separate_app_files(self):
        js=(ROOT/'ui'/'judge'/'app.js').read_text()
        self.assertIn('DEMONSTRATION ONLY',js)
        self.assertIn('X-VerdictKit-Contract',js)
        self.assertNotIn('localStorage',js)
        self.assertNotIn('innerHTML',js)
    def test_no_external_assets(self):
        html=(ROOT/'ui'/'judge'/'index.html').read_text()
        self.assertNotIn('https://',html)
if __name__=='__main__':unittest.main(verbosity=2)
