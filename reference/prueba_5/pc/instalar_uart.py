#!/usr/bin/env python3
"""Transfiere carpeta milkv por USB/UART a /root/osciloscopio_final/milkv.
Requiere consola shell root lista en UART0, y minicom cerrado.
No cambia kernel, no requiere SSH, Ethernet ni login por red.
"""
import argparse
import base64
import hashlib
import io
from pathlib import Path
import sys
import tarfile
import time

ROOT = Path(__file__).resolve().parents[1]


def collect(port, marker, timeout):
    deadline = time.monotonic() + timeout
    result = bytearray()
    marker = marker.encode()
    while time.monotonic() < deadline:
        incoming = port.read(256)
        if incoming:
            result.extend(incoming)
            if marker in result: return bytes(result)
            if len(result) > 8000: del result[:-4000]
    raise RuntimeError('Sin respuesta: '+marker.decode(errors='replace')+'; salida UART: '+repr(bytes(result[-600:])))


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--port', default='/dev/ttyUSB0')
    p.add_argument('--baud', type=int, default=115200)
    args=p.parse_args()
    try:
        import serial
    except ImportError:
        raise SystemExit('Falta pyserial en el PC: python3 -m pip install pyserial')
    buf=io.BytesIO()
    with tarfile.open(fileobj=buf,mode='w:gz') as tar:
        tar.add(ROOT/'milkv',arcname='osciloscopio_final/milkv')
    b64=base64.b64encode(buf.getvalue())
    lines=b'\n'.join(b64[i:i+76] for i in range(0,len(b64),76))+b'\n'
    checksum=hashlib.sha256(lines).hexdigest()
    print('Bytes comprimidos:',len(buf.getvalue()),'texto UART:',len(lines))
    with serial.Serial(args.port,args.baud,timeout=.1,write_timeout=4) as port:
        port.reset_input_buffer()
        port.write(b'\r')
        time.sleep(.1)
        port.write(b'printf "SCOPE_UID:"; id -u\r')
        collect(port,'SCOPE_UID:0',6)
        print('Consola root detectada; copiando el proyecto...')
        port.write(b'stty -echo; mkdir -p /root; cat > /tmp/osc_final.b64 <<\'FIN_SCOPE_B64\'\r')
        time.sleep(.2)
        for start in range(0,len(lines),228):
            port.write(lines[start:start+228]);port.flush();time.sleep(.025)
        port.write(b'FIN_SCOPE_B64\r')
        time.sleep(.1)
        cmd=(f'stty echo; if [ "$(sha256sum /tmp/osc_final.b64 | cut -d" " -f1)" = "{checksum}" ]; then '
             f'base64 -d /tmp/osc_final.b64 > /tmp/osc_final.tgz && '
             f'tar -xzf /tmp/osc_final.tgz -C /root && echo SCOPE_UPLOAD_OK; '
             f'else echo SCOPE_BAD_CHECKSUM; fi\r')
        port.write(cmd.encode())
        output=collect(port,'SCOPE_UPLOAD_OK',20)
        if b'SCOPE_UPLOAD_OK' not in output:
            raise RuntimeError('Error verificación UART: '+repr(output[-1200:]))
        print('Transferencia comprobada por SHA256. Archivos en /root/osciloscopio_final/milkv/')
    print('Abre Minicom y ejecuta: sh /root/osciloscopio_final/milkv/instalar.sh')

if __name__=='__main__':
    try: main()
    except Exception as exc:
        print('ERROR:',exc,file=sys.stderr)
        sys.exit(1)
