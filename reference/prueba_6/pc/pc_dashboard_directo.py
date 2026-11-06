#!/usr/bin/env python3
"""Datos ADC reales por USB ST-LINK virtual COM, NO Milk-V/SPI.
Sólo stdlib, Debian / Linux: python3 pc_dashboard_directo.py --serial /dev/ttyACM0
"""
import argparse
import binascii
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import select
import sys
import termios
import threading
import time
import tty

ROOT = Path(__file__).resolve().parent
LOCK = threading.Lock()
STATE = dict(status='iniciando',valid=False,error='Esperando USB de STM32…',source='hardware',
             requested_preset=2,measured_preset=None,rate_hz=None,sequence=None,
             samples=[],transfer_s=None,effective_bps=None,last_update=None,cycle=0)
SER = None

class StmPort:
    def __init__(self,path):
        self.path=path
        self.fd=os.open(path,os.O_RDWR|os.O_NOCTTY|os.O_NONBLOCK)
        tty.setraw(self.fd,termios.TCSANOW)
        conf=termios.tcgetattr(self.fd)
        conf[4]=termios.B115200; conf[5]=termios.B115200
        conf[2] |= termios.CLOCAL|termios.CREAD|termios.CS8
        conf[2] &= ~(termios.PARENB|termios.CSTOPB|termios.HUPCL)
        if hasattr(termios,'CRTSCTS'): conf[2] &= ~termios.CRTSCTS
        termios.tcsetattr(self.fd,termios.TCSANOW,conf)
        self.running=True
        self.thread=threading.Thread(target=self.read_loop,daemon=True)
        self.thread.start()
    def send_preset(self,preset):
        os.write(self.fd,('P%d\n'%preset).encode())
    def read_loop(self):
        incoming=bytearray()
        while self.running:
            try:
                ready,_,_=select.select([self.fd],[],[],.5)
                if not ready: continue
                b=os.read(self.fd,4096)
                if not b: continue
                incoming.extend(b)
                if len(incoming)>10000:
                    incoming.clear()
                    continue
                while b'\n' in incoming:
                    line,_,remainder=incoming.partition(b'\n')
                    incoming=bytearray(remainder)
                    line=line.strip(b'\r\x00 ')
                    if line.startswith(b'SC,'):
                        self.process(line)
                    elif line.startswith(b'SCOPE_BOOT'):
                        print('STM32 inició:',line.decode('ascii','replace'),flush=True)
            except (OSError,ValueError) as e:
                self.failure('Puerto serial desconectado: '+str(e))
                break
    def failure(self,msg):
        with LOCK:
            STATE.update(status='error',valid=False,error=msg,samples=[],last_update=time.time())
        print('ERROR:',msg,flush=True)
    def process(self,line):
        try:
            payload,crc_text=line.rsplit(b',',1)
            expected=int(crc_text.decode('ascii'),16)
            actual=binascii.crc_hqx(payload,0xFFFF)
            if actual != expected:
                raise ValueError('CRC erróneo: trama UART corrupta')
            items=payload.decode('ascii').split(',')
            if len(items)!=132 or items[0]!='SC':
                raise ValueError('Trama incompleta, %d campos (esperados 132)'%len(items))
            seq,preset,status=map(int,items[1:4])
            if preset not in (1,2,3): raise ValueError('Preset fuera de rango')
            if status:
                raise ValueError('STM32 error ADC/temporizador %d%s'%(status, ' (muestreo demasiado rápido)' if status==17 else ''))
            nums=list(map(int,items[4:]))
            if len(nums)!=128 or not all(0<=n<=4095 for n in nums):
                raise ValueError('Muestras ADC inválidas')
            rate={1:100,2:1000,3:10000}[preset]
            rows=[dict(t=i/rate,ch1=round(nums[2*i]*3.3/4095,5),
                       ch2=round(nums[2*i+1]*3.3/4095,5),
                       adc1=nums[2*i],adc2=nums[2*i+1]) for i in range(64)]
            with LOCK:
                STATE.update(status='ok',valid=True,error=None,source='hardware',
                             measured_preset=preset,rate_hz=rate,sequence=seq,samples=rows,
                             transfer_s=round(len(line)*10/115200,3),effective_bps=115200,
                             last_update=time.time(),cycle=STATE['cycle']+1)
            print('ADC real #%d: %d Sa/s; CH1 %.3f V, CH2 %.3f V'%(
                seq,rate,rows[0]['ch1'],rows[0]['ch2']),flush=True)
        except (ValueError,UnicodeError,OverflowError) as e:
            self.failure(str(e))
    def close(self):
        self.running=False
        os.close(self.fd)

class Web(BaseHTTPRequestHandler):
    def send_body(self,code,body,ctype):
        self.send_response(code)
        self.send_header('Content-Type',ctype)
        self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store')
        self.end_headers()
        self.wfile.write(body)
    def do_GET(self):
        if self.path in ('/','/index.html'):
            return self.send_body(200,(ROOT/'dashboard.html').read_bytes(),'text/html; charset=utf-8')
        if self.path=='/api/state':
            with LOCK: data=dict(STATE)
            if data['last_update'] and time.time()-data['last_update']>8:
                data.update(status='error',valid=False,error='Sin tramas recientes desde STM32',samples=[])
            return self.send_body(200,json.dumps(data).encode(),'application/json')
        self.send_body(404,b'No encontrado','text/plain')
    def do_POST(self):
        if self.path!='/api/preset': return self.send_body(404,b'No encontrado','text/plain')
        try:
            n=int(self.headers.get('Content-Length','0'))
            if n<=0 or n>250: raise ValueError('Longitud inválida')
            p=json.loads(self.rfile.read(n))['preset']
            if type(p)!=int or p not in (1,2,3): raise ValueError('Preset inválido')
            SER.send_preset(p)
            with LOCK: STATE['requested_preset']=p
            return self.send_body(200,json.dumps({'ok':True,'preset':p}).encode(),'application/json')
        except Exception as e:
            return self.send_body(400,json.dumps({'ok':False,'error':str(e)}).encode(),'application/json')
    def log_message(self,*args): pass

def main():
    global SER
    p=argparse.ArgumentParser()
    p.add_argument('--serial',default='/dev/ttyACM0')
    p.add_argument('--http-port',default=8080,type=int)
    args=p.parse_args()
    if not os.path.exists(args.serial):
        raise SystemExit('No existe %s; revisa ls /dev/ttyACM* y cable ST-LINK.'%args.serial)
    SER=StmPort(args.serial)
    try:
        SER.send_preset(2)
    except OSError:
        pass
    web=ThreadingHTTPServer(('127.0.0.1',args.http_port),Web)
    print('ST-LINK USB VCP:',args.serial)
    print('Dashboard: http://127.0.0.1:%d'%args.http_port,flush=True)
    try: web.serve_forever()
    except KeyboardInterrupt: print('\nSaliendo…')
    finally: web.server_close(); SER.close()

if __name__=='__main__': main()
