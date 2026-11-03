import json
import os
import sys
import time
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer
from threading import Thread
sys.path.insert(0, os.path.join(os.path.dirname(__file__),'..','milkv'))
from server import APIHandler, Controller

class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctrl=Controller('simulated','')
        APIHandler.controller=cls.ctrl
        cls.httpd=ThreadingHTTPServer(('127.0.0.1',0),APIHandler)
        cls.base=f'http://127.0.0.1:{cls.httpd.server_port}'
        cls.thread=Thread(target=cls.httpd.serve_forever,daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.ctrl.running=False
        cls.httpd.shutdown();cls.httpd.server_close()

    def call(self, path, data=None):
        req=Request(self.base+path,method='POST' if data is not None else 'GET',
                    data=json.dumps(data).encode() if data is not None else None,
                    headers={'Content-Type':'application/json'})
        try:
            with urlopen(req, timeout=3) as res:
                b=res.read()
                return res.status,json.loads(b) if b else None
        except HTTPError as ex:
            return ex.code,json.loads(ex.read())

    def test_status_and_window(self):
        status, body=self.call('/api/v1/status')
        self.assertEqual(status,200)
        self.assertEqual(body['source'],'simulated')
        self.assertTrue(body['connected'])
        end=time.monotonic()+1.5
        status,win=204,None
        while time.monotonic()<end:
            status,win=self.call('/api/v1/window/latest')
            if status==200: break
            time.sleep(0.06)
        self.assertEqual(status,200)
        self.assertEqual(win['source'],'simulated')
        self.assertEqual(len(win['channels']['ch1']),64)
        self.assertEqual(len(win['channels']['ch2']),64)

    def test_preset_and_revision(self):
        _,before=self.call('/api/v1/status')
        status,result=self.call('/api/v1/acquisition/preset',{'sample_rate_hz':100})
        self.assertEqual(status,200)
        self.assertTrue(result['applied'])
        self.assertEqual(result['source'],'simulated')
        self.assertGreater(result['config_revision'],before['config_revision'])
        status,win=self.call('/api/v1/window/latest')
        self.assertIn(status,(200,204))
        if status==200:
            self.assertEqual(win['config_revision'],result['config_revision'])
            self.assertEqual(win['sample_rate_hz'],100)
        status,err=self.call('/api/v1/acquisition/preset',{'sample_rate_hz':40000})
        self.assertEqual(status,422)
        self.assertEqual(err['error']['code'],'INVALID_PRESET')

if __name__=='__main__':unittest.main()
