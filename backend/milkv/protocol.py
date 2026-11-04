"""Formato binario candidato SPI v0.2 de uCuPViewer.

Las tramas CMD/ACK/WINDOW están documentadas en docs/03_contratos_interfaces_v0_2.txt.
La codificación de estados distintos de OK y de info0/info1 requiere acuerdo con firmware.
Este módulo NO habla con hardware ni simula confirmaciones del STM32.
"""
import binascii
import struct

MAGIC_CMD = 0xA5
MAGIC_RESP = 0x5A
PING, SET_PRESET, START_CAPTURE, GET_STATUS, READ_WINDOW = 1, 2, 3, 4, 5

# Propuesta LOCAL para pruebas, no codificación de estados aprobada por firmware.
OK, BUSY, BAD_CMD, BAD_CRC, NO_WINDOW, OVERRUN = range(6)
RATE_TO_ID = {100: 0, 1000: 1, 10000: 2}
ID_TO_RATE = {v: k for k, v in RATE_TO_ID.items()}


class ProtocolError(Exception):
    pass


class BusyError(ProtocolError):
    pass


def crc16(data: bytes) -> int:
    """CRC-16/CCITT-FALSE: polinomio 0x1021, init 0xFFFF, refin/refout false."""
    return binascii.crc_hqx(data, 0xFFFF)


def command(opcode: int, arg: int, seq: int) -> bytes:
    if not 0 <= opcode <= 255 or not 0 <= arg <= 255:
        raise ValueError('Opcode/argumento fuera del rango uint8')
    head = bytes((MAGIC_CMD, opcode, arg, seq & 255, 0, 0))
    return head + struct.pack('<H', crc16(head))


def parse_ack(data: bytes, opcode: int, seq: int) -> tuple[int, int, int]:
    if len(data) != 8:
        raise ProtocolError('ACK debe tener exactamente ocho bytes')
    if data[0] != MAGIC_RESP or data[2] != opcode or data[3] != (seq & 255):
        raise ProtocolError('ACK con magic, opcode o secuencia incorrecta')
    if crc16(data[:6]) != struct.unpack_from('<H', data, 6)[0]:
        raise ProtocolError('ACK con CRC incorrecto')
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
        raise ProtocolError('CRC incorrecto en ventana')
    values = struct.unpack_from('<128H', data, 8)
    if any(v > 4095 for v in values):
        raise ProtocolError('Valor ADC fuera del rango [0..4095]')
    return {'ch1': list(values[0::2]), 'ch2': list(values[1::2])}
