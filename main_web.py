"""WebEngine UI entrypoint."""

from __future__ import annotations

import sys

try:
    from PySide6.QtWidgets import QApplication
except ImportError:  # pragma: no cover
    from PyQt6.QtWidgets import QApplication  # type: ignore

from core.communication_manager import CommunicationManager
from core.event_bus import EventBus
from core.plugin_manager import PluginManager
from core.protocol_loader import ProtocolLoader
from ui.web_window import WebWindow


def main() -> None:
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
