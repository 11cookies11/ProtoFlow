from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class ChartBridge(QObject):  # pragma: no cover - thin signal wrapper
    sig_data = Signal(dict)

    def __init__(self) -> None:
        super().__init__()


chart_bridge = ChartBridge()
