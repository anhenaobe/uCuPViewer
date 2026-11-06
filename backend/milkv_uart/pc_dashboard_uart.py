#!/usr/bin/env python3
"""Osciloscopio por UART sin Ethernet ni paquetes Python externos.
Lanza un capturador en memoria en la consola serial de la Milk-V y
sirve el dashboard HTTP en ESTE PC: http://127.0.0.1:8080
Requiere una sesión root de Milk-V ya abierta por Minicom antes de cerrarlo.
"""
import argparse
import base64
from collections import deque
import json
import math
import os
import pathlib
import queue
import re
import select
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = pathlib.Path(__file__).resolve().parent
STATE_LOCK = threading.Lock()
STATE = dict(status='iniciando',valid=False,error='Esperando la primera lectura UART…',
             source='hardware',requested_preset=2,measured_preset=None,
             rate_hz=None,sequence=None,samples=[],transfer_s=None,
             effective_bps=None,last_update=None,cycle=0)
SERIAL = None

# Bash may prefix command output with OSC shell-integration and CSI sequences.
CONSOLE_ESCAPE = re.compile(
    r'\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\x1b\[[0-?]*[ -/]*[@-~]'
)


def console_line(raw):
    return CONSOLE_ESCAPE.sub('', raw.decode('utf-8', 'replace')).strip('\r\x00 ')


class SerialPort:
    def __init__(self, path):
        if not os.path.exists(path):
            raise RuntimeError('No existe %s. Revisa el adaptador USB-UART.' % path)
        # stty es un programa estándar en Debian; no se necesita pyserial.
        subprocess.run(['stty','-F',path,'115200','raw','-echo','-ixon','-ixoff','-crtscts'],check=True)
        self.fd = os.open(path, os.O_RDWR|os.O_NOCTTY|os.O_NONBLOCK)
        self.lines = queue.Queue()
        self.recent = deque(maxlen=12)
        self.lock = threading.Lock()
        self.running = True
        self.thread = threading.Thread(target=self.reader,daemon=True)
        self.thread.start()

    def reader(self):
        buf = bytearray()
        while self.running:
            try:
                readable,_,_ = select.select([self.fd], [], [], .2)
                if not readable:
                    continue
                data = os.read(self.fd,4096)
                if not data:
                    continue
                buf.extend(data)
                if len(buf)>32000:
                    buf.clear()
                while b'\n' in buf:
                    raw,_,rest = buf.partition(b'\n')
                    buf = bytearray(rest)
                    line = console_line(raw)
                    self.recent.append(line[:200])
                    if line.startswith('SCOPE_DATA '):
                        try:
                            self.handle_data(json.loads(line[len('SCOPE_DATA '):]))
                        except Exception as exc:
                            print('Error interpretando lectura UART:',exc,flush=True)
                    elif line.startswith('SCOPE_PRESET '):
                        print('Milk-V:',line,flush=True)
                    else:
                        self.lines.put(line)
            except (OSError,ValueError) as exc:
                if self.running:
                    print('Lectura serial terminada:',exc,flush=True)
                return

    def handle_data(self,data):
        with STATE_LOCK:
            STATE['cycle'] += 1
            STATE['last_update'] = time.time()
            if data.get('ok'):
                rate_code=data['preset']
                rate={1:100,2:1000,3:10000}[rate_code]
                a,b=data['ch1'],data['ch2']
                if len(a)!=64 or len(b)!=64:
                    raise ValueError('Tamaño ADC inválido')
                samples=[dict(t=i/rate,ch1=round(a[i]*3.3/4095,5),
                              ch2=round(b[i]*3.3/4095,5),adc1=a[i],adc2=b[i])
                         for i in range(64)]
                STATE.update(status='ok',valid=True,error=None,source='hardware',
                             measured_preset=rate_code,rate_hz=rate,
                             sequence=data['sequence'],samples=samples,
                             transfer_s=data['transfer_s'],effective_bps=data['effective_bps'])
                print('Captura #%d válida: %d Sa/s, SPI %.2f s, UART OK' %
                      (data['sequence'],rate,data['transfer_s']),flush=True)
            else:
                msg=data.get('error','Respuesta desconocida')
                STATE.update(status='error',valid=False,error=msg,samples=[])
                print('Sin datos válidos:',msg,flush=True)

    def send(self, text):
        payload=text.encode('utf-8')
        with self.lock:
            while payload:
                _,can_write,_=select.select([], [self.fd], [], 5)
                if not can_write:
                    raise TimeoutError('No se puede escribir por UART')
                n=os.write(self.fd,payload)
                payload=payload[n:]

    def await_line(self,expected,timeout=8):
        until=time.monotonic()+timeout
        while time.monotonic()<until:
            try:
                line=self.lines.get(timeout=max(.01,until-time.monotonic()))
            except queue.Empty:
                break
            if line.startswith(expected):
                return line
        recent='\n'.join(self.recent)
        raise RuntimeError('Sin respuesta %s por UART. Últimos mensajes:\n%s' % (expected,recent))

    def install_remote(self, source):
        # El usuario ya dejó la consola en root@duos por Minicom.
        self.send('\n')
        time.sleep(.3)
        self.send('printf "SCOPE_UID:%s\\n" "$(id -u)"\n')
        self.await_line('SCOPE_UID:0',timeout=6)
        print('Consola root de Milk-V detectada.')
        self.send('stty -echo\n')
        time.sleep(.2)
        bootstrap = (
            'python3 -u -c \'import base64,sys; p=[]; '
            'print("SCOPE_LOADER_READY",flush=True); '
            '[(p.append(base64.b64decode(s.strip())),print("SCOPE_ACK",flush=True)) '
            'for s in iter(sys.stdin.readline,"SCOPE_LOADER_END\\n")]; '
            'exec(compile(b"".join(p),"<uart-scope>","exec"),'
            '{"__name__":"__main__"})\'\n'
        )
        self.send(bootstrap)
        self.await_line('SCOPE_LOADER_READY',timeout=8)
        # Cada bloque espera ACK, para evitar pérdida de caracteres por UART.
        blob=source.read_bytes()
        for pos in range(0,len(blob),270):
            self.send(base64.b64encode(blob[pos:pos+270]).decode()+'\n')
            self.await_line('SCOPE_ACK',timeout=5)
        self.send('SCOPE_LOADER_END\n')
        self.await_line('SCOPE_STARTED',timeout=12)
        print('Capturador SPI activo en Milk-V. UART conectado.')

    def close(self):
        self.running=False
        try:
            self.send('Q\n')
        except (OSError,TimeoutError):
            pass
        time.sleep(.2)
        os.close(self.fd)


class Web(BaseHTTPRequestHandler):
    def send_body(self,code,body,content_type):
        self.send_response(code)
        self.send_header('Content-Type',content_type)
        self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ('/','/index.html'):
            self.send_body(200,(ROOT.parents[1]/'frontend'/'uart_dashboard'/'dashboard.html').read_bytes(),'text/html; charset=utf-8')
        elif self.path=='/api/state':
            with STATE_LOCK:
                data=dict(STATE)
            if data.get('last_update') and time.time()-data['last_update']>15:
                data.update(status='error',valid=False,error='No se reciben datos recientes por UART',samples=[])
            self.send_body(200,json.dumps(data).encode(),'application/json')
        else:
            self.send_body(404,b'No encontrado','text/plain')

    def do_POST(self):
        if self.path!='/api/preset':
            return self.send_body(404,b'No encontrado','text/plain')
        try:
            n=int(self.headers.get('Content-Length','0'))
            if n<1 or n>256:
                raise ValueError('Tamaño inválido')
            p=json.loads(self.rfile.read(n))['preset']
            if type(p)!=int or p not in (1,2,3):
                raise ValueError('Preset inválido')
            SERIAL.send('P%d\n'%p)
            with STATE_LOCK:
                STATE['requested_preset']=p
            self.send_body(200,json.dumps({'ok':True,'preset':p}).encode(),'application/json')
        except Exception as exc:
            self.send_body(400,json.dumps({'ok':False,'error':str(exc)}).encode(),'application/json')

    def log_message(self,*args):
        pass


def demo_worker():
    seq=0
    while True:
        t0=time.monotonic()
        with STATE_LOCK:
            preset=STATE['requested_preset']
        rate={1:100,2:1000,3:10000}[preset]
        rows=[]
        for i in range(64):
            v1=1.65+math.sin(i/63*math.pi*4)*1.0
            v2=.4+2.2*(i%32)/31
            rows.append(dict(t=i/rate,ch1=round(v1,5),ch2=round(v2,5),adc1=round(v1*4095/3.3),adc2=round(v2*4095/3.3)))
        seq+=1
        with STATE_LOCK:
            STATE.update(status='demo',valid=True,error='SIMULACIÓN: no hay muestras reales',source='demo',
                         rate_hz=rate,measured_preset=preset,sequence=seq,samples=rows,
                         transfer_s=0.,effective_bps=0,last_update=time.time(),cycle=seq)
        time.sleep(max(0,4-(time.monotonic()-t0)))


def main():
    global SERIAL
    parser=argparse.ArgumentParser()
    parser.add_argument('--serial',default='/dev/ttyUSB0')
    parser.add_argument('--http-port',default=8080,type=int)
    parser.add_argument('--demo',action='store_true',help='Solo visualización simulada')
    args=parser.parse_args()
    if args.demo:
        threading.Thread(target=demo_worker,daemon=True).start()
        print('DEMO: SIN acceso a la Milk-V ni al ADC')
    else:
        SERIAL=SerialPort(args.serial)
        try:
            SERIAL.install_remote(ROOT/'milkv_stream.py')
        except Exception:
            SERIAL.running=False
            os.close(SERIAL.fd)
            raise
    server=ThreadingHTTPServer(('127.0.0.1',args.http_port),Web)
    print('Dashboard del computador: http://127.0.0.1:%d' % args.http_port,flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nCerrando…')
    finally:
        server.server_close()
        if SERIAL:
            SERIAL.close()


if __name__=='__main__':
    try:
        main()
    except Exception as e:
        print('ERROR:',e,file=sys.stderr)
        print('Abre Minicom, inicia sesión como root, luego sal de Minicom con Ctrl+A y X. '
              'No uses Minicom y este programa simultáneamente.',file=sys.stderr)
        sys.exit(1)
