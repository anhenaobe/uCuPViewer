"""SPI maestro Linux hacia STM32 esclavo; transacciones separadas de SPI v0.2.

REQUIERE spidev Linux habilitado y firmware STM32 con máquina de estados compatible.
El archivo /dev/spidevB.C determina bus B y chip-select C: ¡no se adivina el B!
El retraso entre transacciones es provisional hasta confirmar READY/IRQ o polling.
"""
import re
import time

from protocol import (
    PING, SET_PRESET, START_CAPTURE, GET_STATUS, READ_WINDOW,
    OK, BUSY, NO_WINDOW, RATE_TO_ID,
    BusyError, ProtocolError, command, parse_ack, parse_window,
)


class SPITransport:
    """Compatible con spidev.SpiDev.xfer2; acepta adapter simulado para pruebas."""

    def __init__(self, path='/dev/spidev3.0', speed_hz=1_000_000,
                 ack_delay_ms=5.0, adapter=None):
        match = re.fullmatch(r'/dev/spidev(\d+)\.(\d+)', path)
        if not match:
            raise ValueError('Usa /dev/spidevBUS.CS, según los nodos reales del kernel')
        if not 10_000 <= speed_hz <= 1_000_000:
            raise ValueError('Velocidad inicial entre 10 kHz y 1 MHz, sin validación de máximos')
        if not 0 <= ack_delay_ms <= 500:
            raise ValueError('ack_delay_ms fuera de rango')
        self.path = path
        self.speed_hz = speed_hz
        self.ack_delay_s = ack_delay_ms / 1000.0
        self.seq = 0
        self._owned = adapter is None
        if adapter is None:
            try:
                import spidev
            except ImportError as exc:
                raise OSError('Falta Python spidev: instalar python3-spidev en la Milk-V') from exc
            adapter = spidev.SpiDev()
            adapter.open(int(match.group(1)), int(match.group(2)))
        self.spi = adapter
        self.spi.max_speed_hz = speed_hz
        self.spi.mode = 0
        self.spi.bits_per_word = 8
        if hasattr(self.spi, 'lsbfirst'):
            self.spi.lsbfirst = False

    def close(self):
        if self.spi is not None and self._owned:
            self.spi.close()
        self.spi = None

    def _transfer(self, payload: bytes) -> bytes:
        if self.spi is None:
            raise OSError('SPI cerrado')
        # Cada xfer2 implica una sola activación CS; tres fases: CMD, ACK, WINDOW.
        rx = bytes(self.spi.xfer2(list(payload)))
        if len(rx) != len(payload):
            raise ProtocolError('Transferencia SPI de longitud incorrecta')
        return rx

    def _delay(self):
        if self.ack_delay_s:
            time.sleep(self.ack_delay_s)

    def exchange(self, opcode: int, arg: int = 0):
        seq = self.seq
        self.seq = (self.seq + 1) & 255
        self._transfer(command(opcode, arg, seq))
        # El MCU debe cargar sus bytes ACK ANTES de que generemos relojes.
        self._delay()
        rc, info0, info1 = parse_ack(self._transfer(bytes(8)), opcode, seq)
        if rc == BUSY:
            raise BusyError('STM32 ocupado (valor BUSY provisional)')
        if rc != OK:
            if opcode == READ_WINDOW and rc == NO_WINDOW:
                return None
            raise ProtocolError(f'STM32 respondió código {rc} al opcode {opcode}')
        if opcode == READ_WINDOW:
            # Trama transmitida en una tercera transacción independiente.
            self._delay()
            data = self._transfer(bytes(268))
            return parse_window(data, seq, self.rate)
        return info0, info1

    def ping(self):
        self.exchange(PING)

    def set_preset(self, hz: int):
        if hz not in RATE_TO_ID:
            raise ValueError('Preset no permitido')
        self.exchange(SET_PRESET, RATE_TO_ID[hz])
        self.rate = hz

    def capture_window(self, expected_rate: int):
        self.exchange(START_CAPTURE)
        deadline = time.monotonic() + 2.0
        while True:
            try:
                status, preset_id = self.exchange(GET_STATUS)
            except BusyError:
                status = 1  # Seguimos esperando adquisición, no desconexión.
                preset_id = RATE_TO_ID[expected_rate]
            if preset_id != RATE_TO_ID[expected_rate]:
                raise ProtocolError('GET_STATUS reporta un preset diferente')
            # Interpretación PROVISIONAL de info0 en ACK de GET_STATUS:
            # 0=idle, 1=adquiriendo, 2=lista, 3=error (no está aprobada en v0.2).
            if status == 2:
                break
            if status == 3:
                raise ProtocolError('STM32 reporta ERROR de ADC/DMA')
            if status not in (0, 1):
                raise ProtocolError(f'Estado de captura desconocido: {status}')
            if time.monotonic() >= deadline:
                raise TimeoutError('La ventana ADC no quedó lista antes del timeout')
            time.sleep(0.010)
        self.rate = expected_rate
        window = self.exchange(READ_WINDOW)
        if window is None:
            raise ProtocolError('No existe ventana tras READY')
        return window
