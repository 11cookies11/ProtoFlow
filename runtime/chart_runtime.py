from __future__ import annotations

import random
import time
from typing import Dict, Iterable, List

from PySide6.QtCore import QObject, QTimer, Signal


class ChartRuntime(QObject):
    """Simple runtime bridge that emits parsed data dicts."""

    data_ready = Signal(dict)

    def __init__(self, keys: Iterable[str], interval_ms: int = 200) -> None:
        super().__init__()
        self.keys: List[str] = list(keys)
        self.timer = QTimer(self)
        self.timer.setInterval(interval_ms)
        self.timer.timeout.connect(self._tick)

    def start(self) -> None:
        self.timer.start()

    def stop(self) -> None:
        self.timer.stop()

    def push_data(self, payload: Dict[str, float]) -> None:
        """Push parsed data from external sources."""
        self.data_ready.emit(payload)

    def _tick(self) -> None:
        """Emit mock data periodically (for demo)."""
        now = time.time()
        payload: Dict[str, float] = {"ts": now}
        for key in self.keys:
            payload[key] = random.uniform(0, 100)
        self.data_ready.emit(payload)
