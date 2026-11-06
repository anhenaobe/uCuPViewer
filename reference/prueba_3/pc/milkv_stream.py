#!/usr/bin/env python3
"""Se ejecuta en memoria en la Milk-V mediante el puente UART del PC.
Maestro SPI por GPIO; trama SC de 264 B con CRC; comunica capturas por UART0.
No altera kernel, pinmux ni servicios. Requiere preparar_gpio.sh previamente.
"""
import json
import os
import select
import sys
import time

BASE = '/sys/class/gpio'
MOS, MIS, CLK, CS = 461, 462, 463, 464
FRAME_LEN = 264
N = 64
HALF = .0002
PRESETS = {1: 100, 2: 1000, 3: 10000}


def w(fd, val):
    os.lseek(fd, 0, os.SEEK_SET)
    os.write(fd, b'1' if val else b'0')


def r(fd):
    os.lseek(fd, 0, os.SEEK_SET)
    return int(os.read(fd, 2).strip())


def crc16(data):
    c = 0xffff
    for b in data:
        c ^= b << 8
        for _ in range(8):
            if c & 0x8000:
                c = ((c << 1) ^ 0x1021) & 0xffff
            else:
                c = (c << 1) & 0xffff
    return c


def capture(pins, preset):
    mo, mi, ck, cs = pins
    tx = bytes((preset,)) + bytes(FRAME_LEN-1)
    rx = bytearray()
    w(cs, 1)
    w(ck, 0)
    w(mo, 0)
    time.sleep(.02)
    t0 = time.monotonic()
    try:
        w(cs, 0)
        time.sleep(.015)
        for b in tx:
            v = 0
            for bit in range(7, -1, -1):
                w(mo, (b >> bit) & 1)
                time.sleep(HALF)
                w(ck, 1)
                time.sleep(HALF)
                v = (v << 1) | r(mi)
                w(ck, 0)
                time.sleep(HALF)
            rx.append(v)
    finally:
        w(cs, 1)
        w(ck, 0)
        w(mo, 0)
    elapsed = time.monotonic() - t0
    if rx[:2] != b'SC':
        raise ValueError('Cabecera incorrecta: ' + bytes(rx[:8]).hex(' '))
    if crc16(rx[:-2]) != int.from_bytes(rx[-2:], 'little'):
        raise ValueError('CRC incorrecto: ' + bytes(rx[:8]).hex(' '))
    rate_code, status = rx[2], rx[3]
    if rate_code not in PRESETS:
        raise ValueError('Preset inválido: ' + str(rate_code))
    if status:
        raise ValueError('STM32 informó código de error 0x%02X' % status)
    ch1, ch2 = [], []
    for i in range(N):
        p = 6+i*4
        a = int.from_bytes(rx[p:p+2], 'little')
        b = int.from_bytes(rx[p+2:p+4], 'little')
        if a > 4095 or b > 4095:
            raise ValueError('Dato ADC fuera de rango en muestra %d' % i)
        ch1.append(a)
        ch2.append(b)
    seq = int.from_bytes(rx[4:6], 'little')
    return dict(ok=True, preset=rate_code, sequence=seq,
                ch1=ch1, ch2=ch2, transfer_s=round(elapsed,3),
                effective_bps=round(FRAME_LEN*8/elapsed))


def emit(data):
    print('SCOPE_DATA '+json.dumps(data,separators=(',',':')),flush=True)


def main():
    pins = tuple(os.open('%s/gpio%d/value' % (BASE, p), flags)
                 for p,flags in ((MOS,os.O_WRONLY),(MIS,os.O_RDONLY),
                                 (CLK,os.O_WRONLY),(CS,os.O_WRONLY)))
    preset = 2
    print('SCOPE_STARTED',flush=True)
    try:
        while True:
            t0 = time.monotonic()
            try:
                obj = capture(pins,preset)
            except Exception as ex:
                obj = dict(ok=False,error=str(ex),preset=preset)
            emit(obj)
            # El maestro lee nuevos comandos P1, P2, P3 durante la pausa.
            while time.monotonic()-t0 < 4.0:
                can_read,_,_ = select.select([sys.stdin], [], [], .10)
                if not can_read:
                    continue
                cmd = sys.stdin.readline().strip()
                if cmd in ('P1','P2','P3'):
                    preset = int(cmd[1])
                    print('SCOPE_PRESET '+str(preset),flush=True)
                elif cmd == 'Q':
                    return
    finally:
        try:
            w(pins[3],1)
            w(pins[2],0)
        except OSError:
            pass
        for fd in pins:
            os.close(fd)
        os.system('stty echo')


if __name__ == '__main__':
    try:
        main()
    except Exception as ex:
        emit(dict(ok=False,error='Inicio fallido: '+str(ex),preset=2))
        raise
