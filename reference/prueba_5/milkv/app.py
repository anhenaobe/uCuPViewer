#!/usr/bin/env python3
"""SBC real: 64x2 ADC vía SPI software, HTTP en Milk-V, proxy Nginx.
Sin pip: usa exclusivamente biblioteca estándar de Python3.
"""
import argparse
import csv
import io
import json
import pathlib
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from protocolo import decode
import sys

ROOT = pathlib.Path(__file__).resolve().parent
LOCK = threading.Lock()
PERIOD = 4.0  # 0.25Hz
STATE = dict(status='iniciando', ok=False, requested_preset=2,
             preset=None, rate_hz=None, sequence=None, samples=[],
             transfer_s=None, effective_bps=None, last_update=None,
             error=None, success_count=0, error_count=0, source='STM32 ADC')


def command(preset):
    binary = ROOT / 'spi_master'
    if binary.is_file() and binary.stat().st_mode & 0o111:
        return [str(binary), str(preset), '200']
    return [sys.executable, str(ROOT / 'spi_master.py'), str(preset)]


def worker():
    while True:
        start = time.monotonic()
        with LOCK:
            preset = STATE['requested_preset']
        try:
            t0 = time.monotonic()
            proc = subprocess.run(command(preset),
                                  timeout=3.4, capture_output=True, check=True)
            elapsed = time.monotonic() - t0
            data = decode(proc.stdout)
            with LOCK:
                STATE.update(data)
                STATE.update(status='correcto', ok=True, error=None,
                             requested_preset=preset, last_update=time.time(),
                             transfer_s=round(elapsed, 3),
                             effective_bps=round(264*8/elapsed),
                             success_count=STATE['success_count'] + 1)
            print(f'OK seq={data["sequence"]}, {data["rate_hz"]} Sa/s, SPI={elapsed:.3f}s',flush=True)
        except Exception as exc:
            msg = str(exc)
            if isinstance(exc, subprocess.CalledProcessError):
                msg = exc.stderr.decode(errors='replace')[-500:] or msg
            with LOCK:
                STATE.update(status='error', ok=False, error=msg,
                             samples=[], last_update=time.time(),
                             error_count=STATE['error_count'] + 1)
            print('ERROR SPI/ADC:', msg, flush=True)
        time.sleep(max(0.0, PERIOD - (time.monotonic() - start)))


class Handler(BaseHTTPRequestHandler):
    def respond(self, status, body, mime):
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Cache-Control','no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split('?', 1)[0]
        if path in ('/', '/index.html'):
            return self.respond(200, (ROOT/'dashboard.html').read_bytes(), 'text/html; charset=utf-8')
        if path == '/api/state':
            with LOCK: data = dict(STATE)
            return self.respond(200, json.dumps(data).encode(), 'application/json')
        if path == '/api/csv':
            with LOCK: data = dict(STATE)
            if not data['ok'] or not data['samples']:
                return self.respond(409, b'Sin datos ADC validos', 'text/plain')
            buf=io.StringIO()
            w=csv.DictWriter(buf,fieldnames=['t','ch1','ch2','adc1','adc2'])
            w.writeheader();w.writerows(data['samples'])
            self.send_response(200)
            body=buf.getvalue().encode()
            self.send_header('Content-Type','text/csv; charset=utf-8')
            self.send_header('Content-Disposition','attachment; filename="captura.csv"')
            self.send_header('Content-Length',str(len(body)))
            self.end_headers();self.wfile.write(body)
            return
        return self.respond(404,b'No encontrado','text/plain')

    def do_POST(self):
        if self.path != '/api/preset':
            return self.respond(404,b'No encontrado','text/plain')
        try:
            length=int(self.headers.get('Content-Length','0'))
            if length < 1 or length > 100: raise ValueError('Longitud inválida')
            obj=json.loads(self.rfile.read(length))
            if type(obj.get('preset')) is not int or obj['preset'] not in (1,2,3):
                raise ValueError('Preset 1, 2 o 3')
            with LOCK: STATE['requested_preset']=obj['preset']
            return self.respond(200,json.dumps({'ok':True,'preset':obj['preset']}).encode(),'application/json')
        except Exception as exc:
            return self.respond(400,json.dumps({'ok':False,'error':str(exc)}).encode(),'application/json')

    def log_message(self,*args): pass


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--host',default='127.0.0.1')
    p.add_argument('--port',type=int,default=8080)
    p.add_argument('--once',action='store_true',help='Una adquisición sin servidor')
    p.add_argument('--preset',type=int,choices=(1,2,3),default=2)
    args=p.parse_args()
    if args.once:
        start=time.monotonic()
        proc=subprocess.run(command(args.preset),
                            capture_output=True,check=True,timeout=3.4)
        data=decode(proc.stdout)
        print(json.dumps({**{k:v for k,v in data.items() if k!='samples'},
                          'first_5_samples':data['samples'][:5],
                          'transfer_s':round(time.monotonic()-start,3)},indent=2))
        return
    threading.Thread(target=worker,daemon=True).start()
    print(f'HTTP de Milk-V en {args.host}:{args.port}',flush=True)
    ThreadingHTTPServer((args.host,args.port),Handler).serve_forever()

if __name__=='__main__': main()
