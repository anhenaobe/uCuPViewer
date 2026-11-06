"""Ensaya el protocolo SPI sin hardware, con un esclavo SPI3 simulado."""
import os
import struct
import sys
import unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'milkv'))

from protocol import crc16, ProtocolError
from spi_transport import SPITransport


class FakeSPI:
    def __init__(self, corrupt_crc=False):
        self.mode = None
        self.bits_per_word = None
        self.max_speed_hz = None
        self.lsbfirst = None
        self.stage = 'cmd'
        self.preset = 1
        self.seq = 0
        self.opcode = 0
        self.ready = False
        self.transfer_sizes = []
        self.corrupt_crc = corrupt_crc

    def xfer2(self, tx):
        self.transfer_sizes.append(len(tx))
        if self.stage == 'cmd':
            assert len(tx) == 8 and tx[0] == 0xA5
            assert int.from_bytes(bytes(tx[6:8]), 'little') == crc16(bytes(tx[:6]))
            self.opcode, arg, self.seq = tx[1], tx[2], tx[3]
            if self.opcode == 2:
                self.preset = arg
            if self.opcode == 3:
                self.ready = True
            self.stage = 'ack'
            return [0] * len(tx)
        if self.stage == 'ack':
            assert len(tx) == 8
            info0 = 2 if self.opcode == 4 and self.ready else 0
            info1 = self.preset if self.opcode == 4 else 0
            ack = bytes([0x5A, 0, self.opcode, self.seq, info0, info1])
            ack += struct.pack('<H', crc16(ack))
            self.stage = 'window' if self.opcode == 5 else 'cmd'
            return list(ack)
        assert self.stage == 'window' and len(tx) == 268
        frame = bytearray(268)
        frame[:8] = bytes([0x5A, 0, self.seq, self.preset, 64, 0, 0, 1])
        frame[8:264] = struct.pack('<128H', *range(128))
        struct.pack_into('<H', frame, 264, crc16(frame[:264]))
        if self.corrupt_crc:
            frame[10] ^= 1
        self.ready = False
        self.stage = 'cmd'
        return list(frame)


class SPITests(unittest.TestCase):
    def test_three_separate_transactions_window(self):
        fake = FakeSPI()
        link = SPITransport('/dev/spidev3.0', adapter=fake, ack_delay_ms=0)
        self.assertEqual(fake.mode, 0)
        self.assertEqual(fake.bits_per_word, 8)
        self.assertEqual(fake.max_speed_hz, 1000000)
        link.ping()
        link.set_preset(1000)
        win = link.capture_window(1000)
        self.assertEqual(len(win['ch1']), 64)
        self.assertEqual(len(win['ch2']), 64)
        self.assertEqual(win['ch1'][-1], 126)
        self.assertEqual(win['ch2'][-1], 127)
        self.assertEqual(fake.transfer_sizes[-3:], [8, 8, 268])
        link.close()

    def test_rejects_corrupt_window(self):
        link = SPITransport('/dev/spidev3.0', adapter=FakeSPI(corrupt_crc=True), ack_delay_ms=0)
        link.set_preset(100)
        with self.assertRaises(ProtocolError):
            link.capture_window(100)
        link.close()


if __name__ == '__main__':
    unittest.main()
