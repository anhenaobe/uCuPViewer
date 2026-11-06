#!/usr/bin/env python3
"""Respaldo SPI por sysfs GPIO si Milk-V no tiene gcc. stdout SOLO trama binaria.
"""
import os
import sys
import time

PINS = (461, 462, 463, 464)
LEN = 264
HALF = 0.0002

def w(fd, val):
    os.lseek(fd,0,0)
    os.write(fd,b'1' if val else b'0')

def r(fd):
    os.lseek(fd,0,0)
    return os.read(fd,1) == b'1'

def main():
    preset=int(sys.argv[1])
    if preset not in (1,2,3): raise SystemExit('Preset 1/2/3')
    mos=os.open('/sys/class/gpio/gpio461/value',os.O_WRONLY)
    mis=os.open('/sys/class/gpio/gpio462/value',os.O_RDONLY)
    ck=os.open('/sys/class/gpio/gpio463/value',os.O_WRONLY)
    cs=os.open('/sys/class/gpio/gpio464/value',os.O_WRONLY)
    data=bytearray()
    try:
        w(cs,1);w(ck,0);w(mos,0);time.sleep(.02)
        w(cs,0);time.sleep(.015)
        for i in range(LEN):
            val=preset if i==0 else 0
            x=0
            for bit in range(7,-1,-1):
                w(mos,(val>>bit)&1)
                time.sleep(HALF)
                w(ck,1)
                time.sleep(HALF)
                x=(x<<1)|int(r(mis))
                w(ck,0)
                time.sleep(HALF)
            data.append(x)
    finally:
        w(cs,1);w(ck,0);w(mos,0)
        for fd in (mos,mis,ck,cs): os.close(fd)
    sys.stdout.buffer.write(data)

if __name__=='__main__': main()
