"""uCuPViewer prototype: framing for UART, NOT the SPI v0.2 contract."""
import binascii
import os
import select
import struct
import termios
import time
import tty

MAGIC_CMD = 0xA5
MAGIC_RESP = 0x5A
PING, SET_PRESET, START_CAPTURE, GET_STATUS, READ_WINDOW = 1, 2, 3, 4, 5
OK, BUSY, BAD_CMD, BAD_CRC, NO_WINDOW, OVERRUN = range(6)
RATE_TO_ID = {100: 0, 1000: 1, 10000: 2}
ID_TO_RATE = {v: k for k, v in RATE_TO_ID.items()}


class ProtocolError(Exception):
    pass


class BusyError(ProtocolError):
    pass


def crc16(data: bytes) -> int:
    return binascii.crc_hqx(data, 0xFFFF)


def command(opcode: int, arg: int, seq: int) -> bytes:
    head = bytes((MAGIC_CMD, opcode, arg, seq & 255, 0, 0))
    return head + struct.pack('<H', crc16(head))


def parse_ack(data: bytes, opcode: int, seq: int) -> tuple[int, int, int]:
    if (len(data) != 8 or data[0] != MAGIC_RESP or data[2] != opcode
            or data[3] != (seq & 255) or crc16(data[:6]) != struct.unpack('<H', data[6:8])[0]):
        raise ProtocolError('ACK inválido: longitud, magic, opcode, seq o CRC')
    return data[1], data[4], data[5]


def parse_window(data: bytes, seq: int, expected_rate: int) -> dict:
    if len(data) != 268 or data[0] != MAGIC_RESP or data[1] != OK or data[2] != (seq & 255):
        raise ProtocolError('Cabecera/longitud de ventana incorrecta')
    n, payload_size = struct.unpack_from('<HH', data, 4)
    if data[3] not in ID_TO_RATE or ID_TO_RATE[data[3]] != expected_rate:
        raise ProtocolError('Ventana de preset distinto al esperado')
    if n != 64 or payload_size != 256 or data[266:268] != b'\x00\x00':
        raise ProtocolError('N, longitud o padding de ventana incorrectos')
    if crc16(data[:264]) != struct.unpack_from('<H', data, 264)[0]:
        raise ProtocolError('CRC incorrecto en la ventana')
    values = struct.unpack_from('<128H', data, 8)
    if any(x > 4095 for x in values):
        raise ProtocolError('Valor ADC fuera de rango [0..4095]')
    return {'ch1': list(values[0::2]), 'ch2': list(values[1::2])}


class SerialUART:
    """UART 8N1, fd no bloqueante y lectura exacta con timeout."""
    def __init__(self, path: str, baud: int = 115200):
        if baud != 115200:
            raise ValueError('Este prototipo solo admite 115200')
        self.fd = os.open(path, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        try:
            tty.setraw(self.fd, termios.TCSANOW)
            cfg = termios.tcgetattr(self.fd)
            cfg[4] = cfg[5] = termios.B115200
            cfg[2] |= termios.CLOCAL | termios.CREAD
            cfg[2] &= ~termios.CRTSCTS if hasattr(termios, 'CRTSCTS') else cfg[2]
            termios.tcsetattr(self.fd, termios.TCSANOW, cfg)
            termios.tcflush(self.fd, termios.TCIOFLUSH)
        except Exception:
            os.close(self.fd)
            self.fd = None
            raise
        self.seq = 0

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None

    def _read(self, size: int, timeout: float) -> bytes:
        end = time.monotonic() + timeout
        result = bytearray()
        while len(result) < size:
            left = end - time.monotonic()
            if left <= 0:
                raise TimeoutError(f'UART: faltan {size-len(result)} bytes')
            if not select.select([self.fd], [], [], left)[0]:
                raise TimeoutError('UART: timeout de lectura')
            try:
                chunk = os.read(self.fd, size-len(result))
            except BlockingIOError:
                continue
            if chunk:
                result.extend(chunk)
        return bytes(result)

    def _write(self, data: bytes, timeout: float):
        end = time.monotonic() + timeout
        offset = 0
        while offset < len(data):
            left = end-time.monotonic()
            if left <= 0 or not select.select([], [self.fd], [], left)[1]:
                raise TimeoutError('UART: timeout de escritura')
            try:
                offset += os.write(self.fd, data[offset:])
            except BlockingIOError:
                continue
        termios.tcdrain(self.fd)

    def exchange(self, opcode: int, arg: int = 0, timeout: float = 1.0):
        seq = self.seq
        self.seq = (self.seq + 1) & 255
        self._write(command(opcode, arg, seq), timeout)
        ack = parse_ack(self._read(8, timeout), opcode, seq)
        rc, info0, info1 = ack
        if rc == BUSY:
            raise BusyError('STM32 ocupado')
        if rc != OK:
            if opcode == READ_WINDOW and rc == NO_WINDOW:
                return None
            raise ProtocolError(f'STM32 respondió status={rc} para opcode={opcode}')
        if opcode == READ_WINDOW:
            return seq, info0, info1, self._read(268, timeout)
        return info0, info1

    def ping(self):
        info = self.exchange(PING)
        if info[0] != 1:
            raise ProtocolError('Versión de protocolo UART desconocida')

    def set_preset(self, hz: int):
        result = self.exchange(SET_PRESET, RATE_TO_ID[hz])
        if result[0] != RATE_TO_ID[hz]:
            raise ProtocolError('ACK de preset con argumento equivocado')

    def capture_window(self, expected_rate: int) -> dict:
        self.exchange(START_CAPTURE)
        deadline = time.monotonic() + 2.0
        while True:
            status, preset_id = self.exchange(GET_STATUS)
            if preset_id != RATE_TO_ID[expected_rate]:
                raise ProtocolError('Firmware reporta preset distinto durante captura')
            if status == 2:   # ACQ_READY
                break
            if status == 3:   # ACQ_ERROR
                raise ProtocolError('ADC/DMA entró en ERROR')
            if time.monotonic() >= deadline:
                raise TimeoutError('Captura ADC excedió 2 segundos')
            time.sleep(0.010)
        packet = self.exchange(READ_WINDOW)
        if packet is None:
            raise ProtocolError('Ventana desapareció antes de transferir')
        seq, count, preset_id, payload = packet
        if count != 64 or preset_id != RATE_TO_ID[expected_rate]:
            raise ProtocolError('ACK READ_WINDOW inconsistente')
        return parse_window(payload, seq, expected_rate)
