"""WebEngine UI entrypoint."""

from __future__ import annotations

import os
import sys
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
