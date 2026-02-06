from __future__ import annotations

try:
    from PySide6.QtCore import QObject, Signal
except ImportError:  # pragma: no cover - fallback to PyQt6
    try:
        from PyQt6.QtCore import QObject, pyqtSignal as Signal  # type: ignore
    except ImportError:  # pragma: no cover - no Qt
        QObject = None  # type: ignore
        Signal = None  # type: ignore


class ChartBridge(QObject):  # pragma: no cover - thin signal wrapper
    sig_data = Signal(dict)

    def __init__(self) -> None:
        super().__init__()


chart_bridge = ChartBridge() if QObject else None
