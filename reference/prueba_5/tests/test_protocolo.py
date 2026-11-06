"""Pruebas unitarias sin hardware. python3 -m unittest discover -s tests -v"""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'milkv'))
from protocolo import crc16, decode, FRAME_SIZE


def example_frame(rate=2, status=0, seq=3, a=4095,b=0):
    frame=bytearray(FRAME_SIZE)
    frame[:2]=b'SC';frame[2]=rate;frame[3]=status
    frame[4:6]=seq.to_bytes(2,'little')
    for i in range(64):
        frame[6+4*i:8+4*i]=a.to_bytes(2,'little')
        frame[8+4*i:10+4*i]=b.to_bytes(2,'little')
    frame[-2:]=crc16(frame[:-2]).to_bytes(2,'little')
    return frame

class TestProtocol(unittest.TestCase):
    def test_reference_crc(self): self.assertEqual(crc16(b'123456789'),0x29B1)
    def test_two_channel_adc(self):
        d=decode(example_frame())
        self.assertEqual(d['rate_hz'],1000)
        self.assertEqual(d['sequence'],3)
        self.assertEqual(len(d['samples']),64)
        self.assertEqual(d['samples'][0]['adc1'],4095)
        self.assertEqual(d['samples'][0]['adc2'],0)
        self.assertAlmostEqual(d['samples'][0]['ch1'],3.3)
    def test_reject_zero(self):
        with self.assertRaises(ValueError):decode(bytes(FRAME_SIZE))
    def test_reject_repeated_53(self):
        with self.assertRaises(ValueError):decode(bytes([0x53])*FRAME_SIZE)
    def test_reject_crc_error(self):
        f=example_frame();f[10]^=0x1
        with self.assertRaises(ValueError):decode(f)
    def test_reject_invalid_adc(self):
        f=example_frame(a=6000)
        with self.assertRaises(ValueError):decode(f)
    def test_error_firmware(self):
        f=example_frame(status=0x20)
        with self.assertRaises(ValueError):decode(f)

if __name__=='__main__':unittest.main()
