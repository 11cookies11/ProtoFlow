"""应用入口：初始化核心组件与界面。"""

from __future__ import annotations

from pathlib import Path

from core.event_bus import EventBus
from core.plugin_manager import PluginManager
from core.protocol_loader import ProtocolLoader
from core.serial_manager import SerialManager
from ui.main_window import run_app


def bootstrap() -> None:
    bus = EventBus()
    plugins = PluginManager(bus, Path("plugins"))
    plugins.load_all()

    protocol = ProtocolLoader(bus)
    serial = SerialManager(bus)

    run_app(bus, serial)


if __name__ == "__main__":
    bootstrap()
