"""Offline only: no device opens, no serial console, no GPIO writes."""
import importlib.util
import pathlib
import unittest
from unittest.mock import patch
P = pathlib.Path(__file__).resolve().parents[2] / 'backend/milkv_uart/milkv_stream.py'
spec = importlib.util.spec_from_file_location('stream', P)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
class ProtocolTests(unittest.TestCase):
    def frame(self):
        b = bytearray(b'SC\x02\x00\x01\x00')
        for i in range(64):
            b += i.to_bytes(2,'little') + (4095-i).to_bytes(2,'little')
        b += m.crc16(b).to_bytes(2,'little')
        return b
    def capture(self,b):
        bits=iter((v >> i)&1 for v in b for i in range(7,-1,-1))
        with patch.object(m,'w'), patch.object(m,'r',side_effect=lambda fd:next(bits)), patch.object(m.time,'sleep'):
            return m.capture((0,1,2,3),2)
    def test_crc_known_vector(self):
        self.assertEqual(m.crc16(b'123456789'),0x29b1)
    def test_frame(self):
        b=self.frame(); self.assertEqual(len(b),264)
        r=self.capture(b)
        self.assertEqual(r['ch1'],list(range(64)))
        self.assertEqual(r['ch2'],list(range(4095,4031,-1)))
    def test_corruption_rejected(self):
        b=self.frame(); b[10]^=1
        with self.assertRaisesRegex(ValueError,'CRC'):self.capture(b)
    def test_wrong_header_rejected(self):
        b=self.frame(); b[0]=0x5a
        with self.assertRaisesRegex(ValueError,'Cabecera'):self.capture(b)
    def test_adc_error_rejected(self):
        b=self.frame();b[3]=0x17;b[-2:]=m.crc16(b[:-2]).to_bytes(2,'little')
        with self.assertRaisesRegex(ValueError,'error'): self.capture(b)
    def test_out_of_range_rejected(self):
        b=self.frame();b[6:8]=(4096).to_bytes(2,'little');b[-2:]=m.crc16(b[:-2]).to_bytes(2,'little')
        with self.assertRaisesRegex(ValueError,'fuera de rango'): self.capture(b)
    def test_c_layout_matches_fixture(self):
        # Static check of actual C serializer; this does not execute ARM code.
        root=pathlib.Path(__file__).resolve().parents[2]
        c=(root/'firmware/stm32/spi_polling/src/main.c').read_text()
        for token in ('#define FRAME_SIZE  264u','#define DATA_END    262u',
                      'put16(6u + i*4u, a)', 'put16(8u + i*4u, b)',
                      'put16(DATA_END, crc16(tx_frame, DATA_END))',
                      'tx_frame[offset] = (uint8_t)value',
                      'tx_frame[offset + 1u] = (uint8_t)(value >> 8)'):
            self.assertIn(token,c)
    def test_integrated_dashboard_path(self):
        root=pathlib.Path(__file__).resolve().parents[2]
        spec=importlib.util.spec_from_file_location('dashboard',root/'backend/milkv_uart/pc_dashboard_uart.py')
        d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
        self.assertTrue((d.ROOT.parents[1]/'frontend/uart_dashboard/dashboard.html').is_file())
        self.assertTrue((d.ROOT/'milkv_stream.py').is_file())
if __name__=='__main__': unittest.main()
