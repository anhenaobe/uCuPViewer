#!/usr/bin/env python3
"""Primer ensayo: 64 muestras por canal desde una NUCLEO-L432KC.
Uso: python3 osc_spi.py 1  (100 Sa/s)
     python3 osc_spi.py 2  (1000 Sa/s)
     python3 osc_spi.py 3  (10000 Sa/s)
El comando seleccionado se aplica a la captura SIGUIENTE.
"""
import os, sys, time, csv
BASE = '/sys/class/gpio'
PINS = {'mosi':461, 'miso':462, 'sck':463, 'cs':464}
N = 64
FRAME_SIZE = 4 + N*4
DELAY = 0.0002  # prueba lenta, NO velocidad definitiva

def open_pin(pin, flags):
    return os.open(f'{BASE}/gpio{pin}/value', flags)

def write(fd, value):
    os.lseek(fd, 0, os.SEEK_SET)
    os.write(fd, b'1' if value else b'0')

def read(fd):
    os.lseek(fd, 0, os.SEEK_SET)
    return int(os.read(fd, 2).strip())

def transfer_byte(value, mosi, miso, sck):
    received = 0
    for bit in range(7, -1, -1):
        write(mosi, (value >> bit) & 1)
        time.sleep(DELAY)
        write(sck, 1)
        time.sleep(DELAY)
        received = (received << 1) | read(miso)
        write(sck, 0)
    return received

def exchange(preset):
    f = {name: open_pin(pin, os.O_RDONLY if name=='miso' else os.O_WRONLY)
         for name,pin in PINS.items()}
    try:
        write(f['cs'], 1)
        write(f['sck'], 0)
        write(f['mosi'], 0)
        time.sleep(0.1)
        tx = bytes([preset]) + bytes(FRAME_SIZE - 1)
        rx = bytearray()
        start = time.monotonic()
        write(f['cs'], 0)
        time.sleep(0.01)
        for b in tx:
            rx.append(transfer_byte(b,f['mosi'],f['miso'],f['sck']))
        write(f['cs'], 1)
        elapsed = time.monotonic() - start
        return rx, elapsed
    finally:
        write(f['cs'], 1)
        write(f['sck'], 0)
        for handle in f.values(): os.close(handle)

def main():
    preset = int(sys.argv[1]) if len(sys.argv)>1 else 2
    if preset not in (1,2,3):
        sys.exit('Preset: 1=100, 2=1000, 3=10000')
    data, seconds = exchange(preset)
    print(f'SPI: {len(data)} bytes en {seconds:.3f} s, {len(data)*8/seconds:.0f} bit/s efectivos')
    print('Cabecera recibida:', data[:8].hex(' '))
    if data[0:2] != b'SC':
        sys.exit('Cabecera incorrecta: revisar NSS, SPI modo 0 y sincronización. NO hay muestras válidas.')
    rate = {1:100,2:1000,3:10000}.get(data[2])
    if rate is None:
        sys.exit('Preset de respuesta inválido')
    with open('captura.csv','w',newline='') as out:
        writer = csv.writer(out)
        writer.writerow(['tiempo_s','canal_1_V','canal_2_V','adc_1','adc_2'])
        for i in range(N):
            pos = 4+4*i
            a = int.from_bytes(data[pos:pos+2],'little')
            b = int.from_bytes(data[pos+2:pos+4],'little')
            writer.writerow([f'{i/rate:.6f}', f'{a*3.3/4095:.5f}', f'{b*3.3/4095:.5f}', a, b])
            if i < 5: print(f'{i:02d}: CH1={a:4d}, CH2={b:4d}')
    print('Muestras guardadas: captura.csv')
    print(f'Captura recibida: {rate} Sa/s, secuencia {data[3]}')
    print('El preset enviado se aplica a la SIGUIENTE lectura. Esperar >1 segundo antes de repetir.')

if __name__=='__main__': main()
