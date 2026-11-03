#!/usr/bin/env python3
"""Usar SOLO con puente temporal UART2 TX↔RX y STM desconectado."""
import argparse
from protocol import SerialUART

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--device', default='/dev/ttyS2')
    args=p.parse_args()
    link=SerialUART(args.device)
    try:
        expected=b'uCuP UART2 LOOPBACK 0123456789\n'
        link._write(expected, 1.0)
        received=link._read(len(expected), 1.0)
        print('Recibido:',repr(received))
        if received != expected:
            raise RuntimeError('Loopback falló: bytes no coinciden')
        print('PASS: TX/RX de UART2 operativos (prueba local, NO STM32)')
    finally:
        link.close()

if __name__=='__main__':main()
