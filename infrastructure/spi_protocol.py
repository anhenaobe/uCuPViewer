"""SPI framing helpers for the uCuPViewer Raspberry Pi controller.

The byte layout follows the proposed contract in docs/03_contratos_interfaces_v0_2.txt.
Command/ACK timing and status-code meanings still require agreement with firmware.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
import struct
from typing import Protocol, Sequence

SYNC_COMMAND = 0xA5
SYNC_RESPONSE = 0x5A

OP_PING = 0x01
OP_SET_PRESET = 0x02
OP_START_CAPTURE = 0x03
OP_GET_STATUS = 0x04
OP_READ_WINDOW = 0x05

COMMAND_SIZE = 8
ACK_SIZE = 8
WINDOW_SIZE = 268
WINDOW_SAMPLES_PER_CHANNEL = 64
WINDOW_PAYLOAD_SIZE = 256
ADC_MAX_RAW = 0x0FFF

# Names kept aligned with the team protocol document and the supplied draft.
HEADER_CMD = SYNC_COMMAND
HEADER_ACK = SYNC_RESPONSE
OPCODE_PING = OP_PING
OPCODE_SET_PRESET = OP_SET_PRESET
OPCODE_START_CAPTURE = OP_START_CAPTURE
OPCODE_GET_STATUS = OP_GET_STATUS
OPCODE_READ_WINDOW = OP_READ_WINDOW
PRESET_100HZ = 0
PRESET_1000HZ = 1
PRESET_10000HZ = 2
PRESET_40000HZ = 3


class SpiProtocolError(ValueError):
    """Raised when an SPI response does not match the proposed wire format."""


class SpiDevice(Protocol):
    """Subset of the spidev object used by this module."""

    mode: int
    bits_per_word: int
    lsbfirst: bool
    cshigh: bool
    max_speed_hz: int

    def open(self, bus: int, device: int) -> None: ...

    def xfer2(
        self,
        values: Sequence[int],
        speed_hz: int = 0,
        delay_usec: int = 0,
        bits_per_word: int = 0,
    ) -> list[int]: ...

    def close(self) -> None: ...


@dataclass(frozen=True)
class Ack:
    status: int
    opcode: int
    sequence: int
    information: int


@dataclass(frozen=True)
class Window:
    status: int
    sequence: int
    preset_id: int
    ch1: tuple[int, ...]
    ch2: tuple[int, ...]


def crc16_ccitt_false(data: bytes | bytearray | memoryview) -> int:
    """CRC-16/CCITT-FALSE: poly=0x1021, init=0xFFFF, refin/refout=False, xorout=0."""
    crc = 0xFFFF
    for value in data:
        crc ^= value << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def _byte(name: str, value: int) -> int:
    if not isinstance(value, int) or not 0 <= value <= 0xFF:
        raise ValueError(f"{name} must be an integer from 0 to 255")
    return value


def build_command(opcode: int, argument: int = 0, sequence: int = 0) -> bytes:
    """Build the proposed 8-byte command, storing its CRC little-endian."""
    prefix = bytes(
        (SYNC_COMMAND, _byte("opcode", opcode), _byte("argument", argument),
         _byte("sequence", sequence), 0, 0)
    )
    return prefix + crc16_ccitt_false(prefix).to_bytes(2, "little")


def build_cmd_frame(opcode: int, arg: int = 0, seq: int = 0) -> bytes:
    """Compatibility spelling used by the supplied SPI protocol draft."""
    return build_command(opcode, arg, seq)


def parse_ack(
    response: bytes | bytearray | Sequence[int],
    *,
    expected_opcode: int | None = None,
    expected_sequence: int | None = None,
) -> Ack:
    """Validate an ACK and optional opcode/sequence echoes.

    Status-code meanings remain raw until the team freezes their mapping.
    """
    raw = bytes(response)
    if len(raw) != ACK_SIZE:
        raise SpiProtocolError(f"ACK must be {ACK_SIZE} bytes, received {len(raw)}")
    if raw[0] != SYNC_RESPONSE:
        raise SpiProtocolError(f"invalid ACK sync byte: 0x{raw[0]:02X}")

    received_crc = int.from_bytes(raw[6:8], "little")
    calculated_crc = crc16_ccitt_false(raw[:6])
    if received_crc != calculated_crc:
        raise SpiProtocolError(
            f"ACK CRC mismatch: received 0x{received_crc:04X}, "
            f"calculated 0x{calculated_crc:04X}"
        )

    ack = Ack(raw[1], raw[2], raw[3], int.from_bytes(raw[4:6], "little"))
    if expected_opcode is not None and ack.opcode != expected_opcode:
        raise SpiProtocolError(
            f"ACK opcode echo 0x{ack.opcode:02X} does not match 0x{expected_opcode:02X}"
        )
    if expected_sequence is not None and ack.sequence != expected_sequence:
        raise SpiProtocolError(
            f"ACK sequence {ack.sequence} does not match {expected_sequence}"
        )
    return ack


def parse_ack_frame(
    data: bytes | bytearray | Sequence[int],
    expected_opcode: int | None = None,
    expected_seq: int | None = None,
) -> dict[str, object]:
    """Dictionary-returning wrapper used by simple scripts and the mock demo."""
    try:
        ack = parse_ack(
            data,
            expected_opcode=expected_opcode,
            expected_sequence=expected_seq,
        )
    except (SpiProtocolError, ValueError) as exc:
        return {"valid": False, "error": str(exc)}
    return {
        "valid": True,
        "header": HEADER_ACK,
        "status": ack.status,
        "opcode_eco": ack.opcode,
        "seq_eco": ack.sequence,
        "info_opcional": ack.information,
    }


def parse_window(
    response: bytes | bytearray | Sequence[int],
    *,
    expected_sequence: int | None = None,
) -> Window:
    """Validate and decode the proposed 268-byte READ_WINDOW response."""
    raw = bytes(response)
    if len(raw) != WINDOW_SIZE:
        raise SpiProtocolError(
            f"window must be {WINDOW_SIZE} bytes, received {len(raw)}"
        )
    if raw[0] != SYNC_RESPONSE:
        raise SpiProtocolError(f"invalid window sync byte: 0x{raw[0]:02X}")

    sequence = raw[2]
    if expected_sequence is not None and sequence != expected_sequence:
        raise SpiProtocolError(
            f"window sequence {sequence} does not match {expected_sequence}"
        )

    sample_count = int.from_bytes(raw[4:6], "little")
    payload_size = int.from_bytes(raw[6:8], "little")
    if sample_count != WINDOW_SAMPLES_PER_CHANNEL:
        raise SpiProtocolError(
            f"expected {WINDOW_SAMPLES_PER_CHANNEL} samples per channel, received {sample_count}"
        )
    if payload_size != WINDOW_PAYLOAD_SIZE:
        raise SpiProtocolError(
            f"expected {WINDOW_PAYLOAD_SIZE} payload bytes, received {payload_size}"
        )

    received_crc = int.from_bytes(raw[264:266], "little")
    calculated_crc = crc16_ccitt_false(raw[:264])
    if received_crc != calculated_crc:
        raise SpiProtocolError(
            f"window CRC mismatch: received 0x{received_crc:04X}, "
            f"calculated 0x{calculated_crc:04X}"
        )
    if raw[266:268] != b"\x00\x00":
        raise SpiProtocolError("window padding must be two zero bytes")

    # Payload is 64 interleaved CH1/CH2 pairs of little-endian uint16 values.
    values = tuple(
        int.from_bytes(raw[offset : offset + 2], "little")
        for offset in range(8, 264, 2)
    )
    if any(value > ADC_MAX_RAW for value in values):
        raise SpiProtocolError("window contains a value outside the 12-bit ADC range")

    return Window(raw[1], sequence, raw[3], values[0::2], values[1::2])


def parse_window_frame(
    data: bytes | bytearray | Sequence[int],
    expected_seq: int | None = None,
) -> dict[str, object]:
    """Dictionary-returning wrapper for the proposed READ_WINDOW format."""
    try:
        window = parse_window(data, expected_sequence=expected_seq)
    except (SpiProtocolError, ValueError) as exc:
        return {"valid": False, "error": str(exc)}
    return {
        "valid": True,
        "status": window.status,
        "seq": window.sequence,
        "preset_id": window.preset_id,
        "samples_per_channel": len(window.ch1),
        "payload_bytes": WINDOW_PAYLOAD_SIZE,
        "ch1": list(window.ch1),
        "ch2": list(window.ch2),
    }


class MockSPIDevice:
    """Deterministic SPI fixture that models separate command/ACK/window phases.

    The status values emitted here are mock fixtures only and do not freeze the
    team's status-code mapping or prove hardware behavior.
    """

    MOCK_STATUS_OK = 0x00
    MOCK_STATUS_BAD_CMD = 0x02
    MOCK_STATUS_BAD_CRC = 0x03

    def __init__(self) -> None:
        self.mode = 0
        self.bits_per_word = 8
        self.lsbfirst = False
        self.cshigh = False
        self.max_speed_hz = 1_000_000
        self.is_open = False
        self.preset_id = PRESET_1000HZ
        self.sequence = 0
        self._pending_ack: bytes | None = None
        self._window_pending = False

    def open(self, bus: int, device: int) -> None:
        self.is_open = True

    def close(self) -> None:
        self.is_open = False

    @staticmethod
    def _make_ack(status: int, opcode: int, sequence: int) -> bytes:
        prefix = bytes((HEADER_ACK, status, opcode, sequence, 0, 0))
        return prefix + crc16_ccitt_false(prefix).to_bytes(2, "little")

    def _make_window(self) -> bytes:
        ch1 = [int(2048 + 1500 * math.sin(2 * math.pi * i / 16)) for i in range(64)]
        ch2 = [int(2048 + 1000 * math.cos(2 * math.pi * i / 16)) for i in range(64)]
        interleaved = [sample for pair in zip(ch1, ch2) for sample in pair]
        prefix = struct.pack(
            "<BBBBHH",
            HEADER_ACK,
            self.MOCK_STATUS_OK,
            self.sequence,
            self.preset_id,
            WINDOW_SAMPLES_PER_CHANNEL,
            WINDOW_PAYLOAD_SIZE,
        ) + struct.pack("<128H", *interleaved)
        return prefix + crc16_ccitt_false(prefix).to_bytes(2, "little") + b"\0\0"

    def xfer2(
        self,
        tx_data: Sequence[int],
        speed_hz: int = 0,
        delay_usec: int = 0,
        bits_per_word: int = 0,
    ) -> list[int]:
        if not self.is_open:
            raise OSError("mock SPI device is closed")
        tx = bytes(tx_data)

        # CMD transaction queues its ACK for a later, separate dummy-clock phase.
        if len(tx) == COMMAND_SIZE and tx[0] == HEADER_CMD:
            opcode, argument, sequence = tx[1], tx[2], tx[3]
            valid_crc = int.from_bytes(tx[6:8], "little") == crc16_ccitt_false(tx[:6])
            status = self.MOCK_STATUS_OK
            if not valid_crc:
                status = self.MOCK_STATUS_BAD_CRC
            elif opcode not in {
                OP_PING,
                OP_SET_PRESET,
                OP_START_CAPTURE,
                OP_GET_STATUS,
                OP_READ_WINDOW,
            }:
                status = self.MOCK_STATUS_BAD_CMD
            elif opcode == OP_SET_PRESET:
                if argument not in {PRESET_100HZ, PRESET_1000HZ, PRESET_10000HZ, PRESET_40000HZ}:
                    status = self.MOCK_STATUS_BAD_CMD
                else:
                    self.preset_id = argument
            elif opcode == OP_READ_WINDOW:
                self.sequence = sequence
                self._window_pending = True

            self._pending_ack = self._make_ack(status, opcode, sequence)
            return [0] * len(tx)

        if len(tx) == ACK_SIZE and self._pending_ack is not None:
            ack, self._pending_ack = self._pending_ack, None
            return list(ack)

        if len(tx) == WINDOW_SIZE and self._window_pending:
            self._window_pending = False
            return list(self._make_window())

        return [0] * len(tx)


class SpiLink:
    """Small spidev transport; each method call is a separate CS transaction."""

    def __init__(
        self,
        bus: int = 0,
        device: int = 0,
        speed_hz: int = 1_000_000,
        spi_device: SpiDevice | None = None,
    ) -> None:
        if bus < 0 or device < 0:
            raise ValueError("bus and device must be non-negative")
        if speed_hz <= 0:
            raise ValueError("speed_hz must be positive")
        self.bus = bus
        self.device = device
        self.speed_hz = speed_hz
        self._spi: SpiDevice | None = None
        self._provided_device = spi_device

    def open(self) -> None:
        if self._spi is not None:
            return
        if self._provided_device is not None:
            spi = self._provided_device
        else:
            try:
                import spidev
            except ImportError as exc:
                raise RuntimeError(
                    "Python spidev is not installed; install the python3-spidev package"
                ) from exc
            spi = spidev.SpiDev()
        try:
            spi.open(self.bus, self.device)
            spi.mode = 0  # CPOL=0, CPHA=0
            spi.bits_per_word = 8
            spi.lsbfirst = False
            spi.cshigh = False  # active-low chip select
            spi.max_speed_hz = self.speed_hz
        except Exception:
            try:
                spi.close()
            except Exception:
                pass
            raise
        self._spi = spi

    def close(self) -> None:
        if self._spi is not None:
            self._spi.close()
            self._spi = None

    def __enter__(self) -> "SpiLink":
        self.open()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def _transfer(self, tx: Sequence[int]) -> bytes:
        if self._spi is None:
            raise RuntimeError("SPI link is closed; use it as a context manager")
        rx = self._spi.xfer2(list(tx), self.speed_hz, 0, 8)
        if len(rx) != len(tx):
            raise SpiProtocolError(
                f"SPI returned {len(rx)} bytes for a {len(tx)}-byte transfer"
            )
        return bytes(rx)

    def send_command(self, opcode: int, argument: int = 0, sequence: int = 0) -> None:
        """Send one command transaction; ignore simultaneous MISO bytes."""
        self._transfer(build_command(opcode, argument, sequence))

    def receive_ack(self, opcode: int, sequence: int) -> Ack:
        """Clock out one ACK in its own transaction using eight dummy bytes."""
        return parse_ack(
            self._transfer(bytes(ACK_SIZE)),
            expected_opcode=opcode,
            expected_sequence=sequence,
        )

    def receive_window(self, sequence: int) -> Window:
        """Clock out a complete window with dummy bytes in its own transaction."""
        return parse_window(
            self._transfer(bytes(WINDOW_SIZE)),
            expected_sequence=sequence,
        )


def _run_mock_demo() -> None:
    """Exercise the candidate phases using only the deterministic mock."""
    with SpiLink(spi_device=MockSPIDevice()) as link:
        ping_sequence = 1
        link.send_command(OP_PING, sequence=ping_sequence)
        ping_ack = link.receive_ack(OP_PING, ping_sequence)
        print(f"Mock PING ACK: status=0x{ping_ack.status:02X}")

        window_sequence = 2
        link.send_command(OP_READ_WINDOW, sequence=window_sequence)
        read_ack = link.receive_ack(OP_READ_WINDOW, window_sequence)
        print(f"Mock READ_WINDOW ACK: status=0x{read_ack.status:02X}")
        window = link.receive_window(window_sequence)
        print(f"Mock window: {len(window.ch1)} CH1, {len(window.ch2)} CH2 samples")


if __name__ == "__main__":
    _run_mock_demo()
