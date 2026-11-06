"""uCuPViewer HTTP API. Default mode is explicitly simulated, never hardware."""

from __future__ import annotations

import os
import sys
import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# The deployment installer places spi_protocol.py beside this file. In a repo
# checkout it remains under infrastructure/ to avoid maintaining two copies.
try:
    from spi_protocol import MockSPIDevice, OP_PING, OP_READ_WINDOW, PRESET_100HZ, PRESET_1000HZ, PRESET_10000HZ, SpiLink
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from infrastructure.spi_protocol import MockSPIDevice, OP_PING, OP_READ_WINDOW, PRESET_100HZ, PRESET_1000HZ, PRESET_10000HZ, SpiLink


PRESETS = {100: PRESET_100HZ, 1000: PRESET_1000HZ, 10000: PRESET_10000HZ}
SOURCE = "simulated"

app = FastAPI(title="uCuPViewer API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

_lock = threading.Lock()
_sample_rate_hz = 1000
_window_id = 0


class PresetRequest(BaseModel):
    sample_rate_hz: int = Field(ge=1)


def _simulated_window():
    global _window_id
    _window_id = (_window_id + 1) & 0xFF
    with SpiLink(spi_device=MockSPIDevice()) as link:
        link.send_command(OP_PING, sequence=_window_id)
        link.receive_ack(OP_PING, _window_id)
        link.send_command(OP_READ_WINDOW, sequence=_window_id)
        link.receive_ack(OP_READ_WINDOW, _window_id)
        return link.receive_window(_window_id)


@app.get("/api/v1/status")
def status():
    return {
        "connected": False,
        "capture_status": "simulated",
        "sample_rate_hz": _sample_rate_hz,
        "mcu": "stm32l432kc",
        "source": "simulated",
        "hardware_available": False,
    }


@app.get("/api/v1/window/latest")
def latest_window():
    with _lock:
        window = _simulated_window()
        sample_rate = _sample_rate_hz
    return {
        "window_id": _window_id,
        "source": "simulated",
        "sample_rate_hz": sample_rate,
        "samples_per_channel": len(window.ch1),
        "adc_resolution_bits": 12,
        "unit": "adc_counts",
        "channels": {"ch1": list(window.ch1), "ch2": list(window.ch2)},
    }


@app.post("/api/v1/acquisition/preset")
def set_preset(request: PresetRequest):
    global _sample_rate_hz
    if request.sample_rate_hz not in PRESETS:
        raise HTTPException(status_code=422, detail="Supported presets are 100, 1000 and 10000 Sa/s per channel")
    with _lock:
        _sample_rate_hz = request.sample_rate_hz
    # accepted is intentionally distinct from applied: this is only a mock.
    return {"sample_rate_hz": _sample_rate_hz, "accepted": True, "applied": False, "source": "simulated"}


if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("UCUPVIEWER_BACKEND_HOST", "127.0.0.1")
    port = int(os.environ.get("UCUPVIEWER_BACKEND_PORT", "5000"))
    uvicorn.run(app, host=host, port=port)
