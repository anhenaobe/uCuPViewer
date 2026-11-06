"""Console framing regression tests; no serial devices or GPIO are opened."""
import importlib.util
from collections import deque
from pathlib import Path
import queue
import unittest
from unittest.mock import Mock, patch

path = Path(__file__).resolve().parents[2] / 'backend/milkv_uart/pc_dashboard_uart.py'
spec = importlib.util.spec_from_file_location('dashboard', path)
dashboard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dashboard)


class ConsoleTests(unittest.TestCase):
    def test_shell_integration_before_uid(self):
        raw = b'\x1b[?2004l\r\x1b]3008;type=command;user=root\x1b\\SCOPE_UID:0\r'
        self.assertEqual(dashboard.console_line(raw), 'SCOPE_UID:0')

    def test_bell_terminated_osc_and_color(self):
        raw = b'\x1b]0;duos\x07\x1b[32mSCOPE_LOADER_READY\x1b[0m\r'
        self.assertEqual(dashboard.console_line(raw), 'SCOPE_LOADER_READY')

    def test_command_echo_is_not_an_ack(self):
        raw = b'printf "SCOPE_UID:%s\\n" "$(id -u)"'
        self.assertFalse(dashboard.console_line(raw).startswith('SCOPE_UID:0'))

    def test_fragmented_reader_preserves_data(self):
        port = dashboard.SerialPort.__new__(dashboard.SerialPort)
        port.fd = 123
        port.running = True
        port.lines = queue.Queue()
        port.recent = deque(maxlen=12)
        port.handle_data = Mock()
        chunks = [b'\x1b]3008;type=command\x1b',
                  b'\\SCOPE_UID:', b'0\r\nSCOPE_DATA {"ok":false}\n']

        def ready(*args):
            if chunks:
                return [port.fd], [], []
            port.running = False
            return [], [], []

        with patch.object(dashboard.select, 'select', side_effect=ready), \
             patch.object(dashboard.os, 'read', side_effect=lambda *args: chunks.pop(0)):
            port.reader()
        self.assertEqual(port.await_line('SCOPE_UID:0'), 'SCOPE_UID:0')
        port.handle_data.assert_called_once_with({'ok': False})


if __name__ == '__main__':
    unittest.main()
