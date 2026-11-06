"""Protocolo CRC16 CCITT-FALSE, comprobación de muestras reales.
Toda trama inválida causa error; nunca dibujar datos inventados.
"""
import struct

FRAME_SIZE = 264
RATES = {1: 100, 2: 1000, 3: 10000}


def crc16(data):
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = (((crc << 1) ^ 0x1021) if crc & 0x8000 else crc << 1) & 0xFFFF
    return crc


def decode(frame):
    if len(frame) != FRAME_SIZE:
        raise ValueError(f'Trama de {len(frame)} bytes; esperados {FRAME_SIZE}')
    if frame[:2] != b'SC':
        raise ValueError('Cabecera incorrecta: ' + frame[:8].hex(' '))
    crc_received = int.from_bytes(frame[-2:], 'little')
    crc_calculated = crc16(frame[:-2])
    if crc_received != crc_calculated:
        raise ValueError(f'CRC incorrecto: {crc_received:04x} != {crc_calculated:04x}')
    preset, status = frame[2], frame[3]
    if preset not in RATES:
        raise ValueError(f'Preset desconocido: {preset}')
    if status:
        raise ValueError(f'STM32 informa estado 0x{status:02x} (0x20=esperando ADC, 0x10-0x17=error ADC)')
    seq = int.from_bytes(frame[4:6], 'little')
    rows = []
    for i, (a, b) in enumerate(struct.iter_unpack('<HH', frame[6:262])):
        if a > 4095 or b > 4095:
            raise ValueError(f'Muestra {i} fuera de rango ADC: {a}/{b}')
        rows.append({'t': round(i / RATES[preset], 7),
                     'ch1': round(a * 3.3 / 4095, 5),
                     'ch2': round(b * 3.3 / 4095, 5),
                     'adc1': a, 'adc2': b})
    if len(rows) != 64:
        raise ValueError('Ventana incompleta')
    return {'preset': preset, 'rate_hz': RATES[preset], 'sequence': seq, 'samples': rows}
