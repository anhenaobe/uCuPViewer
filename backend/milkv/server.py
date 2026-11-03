#!/usr/bin/env python3
"""API HTTP para Milk-V Duo S. Sin dependencias pip; Python 3 estándar.
Uso: python3 server.py --simulate
     python3 server.py --device /dev/ttyS2
Source siempre marca si los datos vienen del simulador o del ADC real.
"""
import argparse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
import os
import threading
import time
import uuid

from protocol import SerialUART, ProtocolError, BusyError, RATE_TO_ID

STALE_MS = 6000   # PROPUESTA a validar en el laboratorio


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z')


class Controller:
    def __init__(self, source: str, device: str):
        self.source = source
        self.device = device
        self.rate = 1000
        self.session_id = str(uuid.uuid4())
        self.config_revision = 0
        self.window_id = 0
        self.window = None
        self.window_monotonic = None
        self.connected = source == 'simulated'
        self.capture_status = 'idle' if self.connected else 'unavailable'
        self.error = None
        self.lock = threading.RLock()
        self.io_lock = threading.Lock()
        self.setting = False
        self.transport = None
        self.running = True
        self.worker = threading.Thread(target=self._run, daemon=True)
        self.worker.start()

    def snapshot(self):
        with self.lock:
            return {'connected': self.connected,
                    'capture_status': self.capture_status,
                    'sample_rate_hz': self.rate,
                    'mcu': 'stm32l432kc', 'source': self.source,
                    'session_id': self.session_id,
                    'config_revision': self.config_revision}

    def latest(self):
        with self.lock:
            if not self.connected:
                code = self.error or 'MCU_UNAVAILABLE'
                raise ApiError(504 if code == 'MCU_TIMEOUT' else 503,
                               code, 'Proveedor de adquisición no disponible')
            if self.window is None:
                return None
            copy = dict(self.window)
            copy['is_stale'] = (time.monotonic()-self.window_monotonic)*1000 > STALE_MS
            return copy

    def apply(self, hz):
        if type(hz) is not int or hz not in RATE_TO_ID:
            raise ApiError(422, 'INVALID_PRESET', 'Frecuencia no permitida',
                           {'requested_sample_rate_hz':hz,
                            'allowed_sample_rates_hz':list(RATE_TO_ID)})
        with self.lock:
            if self.setting:
                raise ApiError(409, 'ACQUISITION_BUSY', 'Otro cambio de preset en curso')
            if not self.connected:
                code = self.error or 'MCU_UNAVAILABLE'
                raise ApiError(504 if code == 'MCU_TIMEOUT' else 503,
                               code, 'Proveedor no disponible')
            self.setting = True
            self.capture_status = 'configuring'
        try:
            if self.source == 'hardware':
                if not self.io_lock.acquire(timeout=3.0):
                    raise TimeoutError('Acceso UART bloqueado durante el cambio')
                try:
                    self.transport.set_preset(hz)
                finally:
                    self.io_lock.release()
            with self.lock:
                self.rate = hz
                self.config_revision += 1
                self.window = None
                self.window_monotonic = None
                self.capture_status = 'idle'
                return {'sample_rate_hz':hz, 'applied':True,
                        'source':self.source,'session_id':self.session_id,
                        'config_revision':self.config_revision}
        except TimeoutError as exc:
            self._disconnect('MCU_TIMEOUT', str(exc))
            raise ApiError(504, 'MCU_TIMEOUT', str(exc))
        except (OSError, ProtocolError) as exc:
            self._disconnect('MCU_UNAVAILABLE', str(exc))
            raise ApiError(503,'MCU_UNAVAILABLE',str(exc))
        finally:
            with self.lock:
                self.setting = False

    def _disconnect(self, code, message):
        with self.lock:
            self.connected=False
            self.error=code
            self.capture_status='error' if code == 'MCU_TIMEOUT' else 'unavailable'
        print(f'[UART] {code}: {message}', flush=True)
        # Cerrado en el worker antes del siguiente intento de reconexión.

    def _publish(self, channels, session_id, revision, rate):
        with self.lock:
            if self.session_id != session_id or self.config_revision != revision or self.setting:
                return
            self.window_id += 1
            self.window = {'session_id':session_id,'window_id':self.window_id,
                'config_revision':revision,'captured_at':utc_now(),
                'source':self.source,'sample_rate_hz':rate,
                'samples_per_channel':64,'adc_resolution_bits':12,
                'unit':'adc_counts','channels':channels}
            self.window_monotonic = time.monotonic()
            self.capture_status='ready'

    def _run(self):
        while self.running:
            if self.source == 'simulated':
                with self.lock:
                    revision,rate,sid = self.config_revision,self.rate,self.session_id
                    if not self.setting: self.capture_status='capturing'
                ch1 = [int(2048+1000*math.sin(2*math.pi*4*i/64)) for i in range(64)]
                ch2 = [int(2048+700*math.cos(2*math.pi*3*i/64)) for i in range(64)]
                self._publish({'ch1':ch1,'ch2':ch2},sid,revision,rate)
                time.sleep(0.5)
                continue
            try:
                with self.io_lock:
                    with self.lock:
                        if self.setting:
                            continue
                    if self.transport is None:
                        # No fingir enlace hardware hasta validar una respuesta real del STM32.
                        link = SerialUART(self.device)
                        try:
                            link.ping()
                            link.set_preset(self.rate)
                        except Exception:
                            link.close()
                            raise
                        self.transport = link
                        with self.lock:
                            # Reconexión = nueva sesión; evita reutilizar ventanas previas.
                            self.session_id=str(uuid.uuid4())
                            self.window_id=0
                            self.config_revision=0
                            self.window=None
                            self.window_monotonic=None
                            self.connected=True
                            self.error=None
                            self.capture_status='idle'
                    with self.lock:
                        revision,rate,sid=self.config_revision,self.rate,self.session_id
                        if not self.setting: self.capture_status='capturing'
                    channels = self.transport.capture_window(rate)
                    self._publish(channels,sid,revision,rate)
                time.sleep(0.15)
            except TimeoutError as exc:
                self._disconnect('MCU_TIMEOUT', str(exc))
                if self.transport:
                    self.transport.close(); self.transport=None
                time.sleep(2.0)
            except (OSError, ProtocolError) as exc:
                self._disconnect('MCU_UNAVAILABLE', str(exc))
                if self.transport:
                    self.transport.close(); self.transport=None
                time.sleep(2.0)


class ApiError(Exception):
    def __init__(self, status, code, message, details=None):
        super().__init__(message)
        self.status, self.code, self.message, self.details = status, code, message, details


class APIHandler(BaseHTTPRequestHandler):
    controller = None

    def _send(self, status, data=None):
        raw = b'' if data is None else json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        if raw:
            self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(raw)))
        self.send_header('Cache-Control','no-store')
        self.end_headers()
        if raw: self.wfile.write(raw)

    def _error(self, exc):
        self._send(exc.status,{'error':{'code':exc.code,'message':exc.message,'details':exc.details}})

    def do_GET(self):
        try:
            if self.path == '/api/v1/status':
                return self._send(200, self.controller.snapshot())
            if self.path == '/api/v1/window/latest':
                window=self.controller.latest()
                return self._send(204 if window is None else 200,window)
            raise ApiError(404,'NOT_FOUND','Ruta no encontrada')
        except ApiError as exc:
            self._error(exc)

    def do_POST(self):
        try:
            if self.path != '/api/v1/acquisition/preset':
                raise ApiError(404,'NOT_FOUND','Ruta no encontrada')
            length = int(self.headers.get('Content-Length','-1'))
            if length < 0 or length > 4096:
                raise ApiError(422,'INVALID_PRESET','Cuerpo JSON ausente o demasiado largo')
            try:
                payload=json.loads(self.rfile.read(length))
            except (ValueError, UnicodeDecodeError):
                raise ApiError(422,'INVALID_PRESET','JSON inválido')
            if not isinstance(payload,dict) or set(payload) != {'sample_rate_hz'}:
                raise ApiError(422,'INVALID_PRESET','Se requiere solamente sample_rate_hz')
            self._send(200,self.controller.apply(payload['sample_rate_hz']))
        except ApiError as exc:
            self._error(exc)


def main():
    parser=argparse.ArgumentParser()
    choice=parser.add_mutually_exclusive_group(required=True)
    choice.add_argument('--simulate',action='store_true')
    choice.add_argument('--device',help='UART real, ej. /dev/ttyS2')
    parser.add_argument('--host',default='127.0.0.1')
    parser.add_argument('--port',type=int,default=8080)
    a=parser.parse_args()
    APIHandler.controller=Controller('simulated' if a.simulate else 'hardware',a.device or '')
    httpd=ThreadingHTTPServer((a.host,a.port),APIHandler)
    print(f'HTTP en http://{a.host}:{a.port}, source={APIHandler.controller.source}',flush=True)
    try: httpd.serve_forever()
    except KeyboardInterrupt: pass
    finally:
        APIHandler.controller.running=False
        httpd.server_close()

if __name__=='__main__':main()
