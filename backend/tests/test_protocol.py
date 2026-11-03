import os
import struct
import sys
import unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__),'..','milkv'))
from protocol import crc16, command, parse_ack, parse_window, ProtocolError

class ProtocolTests(unittest.TestCase):
    def test_crc_ccitt_false_reference(self):
        self.assertEqual(crc16(b'123456789'), 0x29B1)

    def test_command(self):
        cmd = command(1, 0, 17)
        self.assertEqual(len(cmd), 8)
        self.assertEqual(cmd[:6], bytes([0xA5,1,0,17,0,0]))
        self.assertEqual(int.from_bytes(cmd[6:],'little'),crc16(cmd[:6]))

    def test_ack_rejects_seq(self):
        d = bytes([0x5A,0,1,4,1,0])
        d += struct.pack('<H',crc16(d))
        self.assertEqual(parse_ack(d,1,4),(0,1,0))
        with self.assertRaises(ProtocolError): parse_ack(d,1,5)

    def test_window_and_crc(self):
        values=[k % 4096 for k in range(128)]
        frame=bytearray(268)
        frame[0:8]=bytes([0x5A,0,9,1,64,0,0,1])
        frame[8:264]=struct.pack('<128H',*values)
        struct.pack_into('<H',frame,264,crc16(frame[:264]))
        out=parse_window(bytes(frame),9,1000)
        self.assertEqual(len(out['ch1']),64)
        self.assertEqual(len(out['ch2']),64)
        self.assertEqual(out['ch1'][:3],[0,2,4])
        self.assertEqual(out['ch2'][:3],[1,3,5])
        frame[11] ^= 1
        with self.assertRaises(ProtocolError):parse_window(bytes(frame),9,1000)

if __name__=='__main__':unittest.main()
