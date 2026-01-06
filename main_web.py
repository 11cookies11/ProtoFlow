"""WebEngine UI entrypoint."""

from __future__ import annotations

import atexit
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

try:
    from PySide6.QtWidgets import QApplication
except ImportError:  # pragma: no cover
    from PyQt6.QtWidgets import QApplication  # type: ignore

from core.communication_manager import CommunicationManager
from core.event_bus import EventBus
from core.plugin_manager import PluginManager
from core.protocol_loader import ProtocolLoader
from ui.web_window import WebWindow


class _TeeStream:
    def __init__(self, primary, file_handle, is_error: bool) -> None:
        self._primary = primary
        self._file = file_handle
        self._is_error = is_error

    def write(self, data: str) -> int:
        if not data:
            return 0
        written = self._primary.write(data)
        self._primary.flush()
        prefix = "[STDERR] " if self._is_error else "[STDOUT] "
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        for line in data.splitlines():
            if not line.strip():
                continue
            self._file.write(f"{timestamp} {prefix}{line}\n")
        self._file.flush()
        return written

    def flush(self) -> None:
        self._primary.flush()
        self._file.flush()


def _setup_run_logging() -> Path:
    log_dir = Path.cwd() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    log_path = log_dir / f"web_ui_{timestamp}.log"
    log_handle = log_path.open("a", encoding="utf-8")
    atexit.register(log_handle.close)

    sys.stdout = _TeeStream(sys.stdout, log_handle, is_error=False)
    sys.stderr = _TeeStream(sys.stderr, log_handle, is_error=True)

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(threadName)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.getLogger("main_web").info("Log file: %s", log_path)
    return log_path


def _detect_d3d11() -> bool:
    if sys.platform != "win32":
        return False
    try:
        import ctypes
    except Exception:
        return False
    try:
        d3d11 = ctypes.WinDLL("d3d11")
    except OSError:
        return False
    try:
        create_device = d3d11.D3D11CreateDevice
    except AttributeError:
        return False
    create_device.argtypes = [
        ctypes.c_void_p,
        ctypes.c_uint,
        ctypes.c_void_p,
        ctypes.c_uint,
        ctypes.POINTER(ctypes.c_uint),
        ctypes.c_uint,
        ctypes.c_uint,
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(ctypes.c_uint),
        ctypes.POINTER(ctypes.c_void_p),
    ]
    create_device.restype = ctypes.c_long
    feature_levels = (ctypes.c_uint * 3)(0xB000, 0xA000, 0x9300)
    device = ctypes.c_void_p()
    context = ctypes.c_void_p()
    chosen = ctypes.c_uint()
    hr = create_device(
        None,
        1,
        None,
        0,
        feature_levels,
        len(feature_levels),
        7,
        ctypes.byref(device),
        ctypes.byref(chosen),
        ctypes.byref(context),
    )
    return hr == 0


def _select_webengine_flags() -> Optional[str]:
    override = os.environ.get("PROTOFLOW_WEBENGINE_FLAGS")
    if override:
        return override
    if sys.platform != "win32":
        return None
    if _detect_d3d11():
        return "--disable-features=DirectComposition --use-angle=d3d11"
    return "--disable-features=DirectComposition"


def main() -> None:
    _setup_run_logging()
    flags = _select_webengine_flags()
    if flags:
        os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", flags)
    bus = EventBus()
    comm = CommunicationManager(bus)
    protocol = ProtocolLoader(bus)
    plugins = PluginManager(bus, protocol=protocol)
    plugins.load_all()

    app = QApplication.instance() or QApplication(sys.argv)
    window = WebWindow(bus=bus, comm=comm)
    window.show()
    print("ProtoFlow Web UI started")
    app.exec()


if __name__ == "__main__":
    main()
