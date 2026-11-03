"""Prueba Linux de transporte físico simulado mediante pseudoterminal POSIX."""
import os
import pty
import select
import struct
import sys
import threading
import unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__),'..','milkv'))
from protocol import SerialUART, crc16, PING, SET_PRESET, START_CAPTURE, GET_STATUS, READ_WINDOW

class PseudoUART(unittest.TestCase):
    def test_full_handshake_window(self):
        master,slave=pty.openpty()
        name=os.ttyname(slave)
        stop=threading.Event()
        errors=[]
        def server():
            buf=bytearray()
            preset=1
            ready=False
            try:
                while not stop.is_set():
                    if not select.select([master],[],[],0.05)[0]: continue
                    chunk=os.read(master,4096)
                    buf.extend(chunk)
                    while len(buf)>=8:
                        cmd=bytes(buf[:8]);del buf[:8]
                        assert cmd[0]==0xA5
                        assert crc16(cmd[:6])==int.from_bytes(cmd[6:8],'little')
                        op,arg,seq=cmd[1:4]
                        if op==SET_PRESET: preset=arg
                        if op==START_CAPTURE: ready=True
                        info0 = 1 if op==PING else (preset if op==SET_PRESET else
                            (2 if ready else 0) if op==GET_STATUS else (64 if op==READ_WINDOW else 0))
                        info1 = preset if op in (GET_STATUS,READ_WINDOW) else 0
                        ack=bytes([0x5A,0,op,seq,info0,info1]);ack+=struct.pack('<H',crc16(ack))
                        os.write(master,ack)
                        if op==READ_WINDOW:
                            f=bytearray(268)
                            f[:8]=bytes([0x5A,0,seq,preset,64,0,0,1])
                            f[8:264]=struct.pack('<128H',*(range(128)))
                            struct.pack_into('<H',f,264,crc16(f[:264]))
                            os.write(master,f)
                            ready=False
            except Exception as e:
                if not stop.is_set():errors.append(e)
        thread=threading.Thread(target=server,daemon=True)
        thread.start()
        link=SerialUART(name)
        try:
            link.ping()
            link.set_preset(1000)
            samples=link.capture_window(1000)
            self.assertEqual(len(samples['ch1']),64)
            self.assertEqual(samples['ch1'][-1],126)
            self.assertEqual(samples['ch2'][-1],127)
            self.assertFalse(errors)
        finally:
            link.close()
            stop.set()
            thread.join(timeout=0.4)
            os.close(master);os.close(slave)

if __name__ == '__main__':unittest.main()
