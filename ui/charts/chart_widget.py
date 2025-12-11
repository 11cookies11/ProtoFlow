from __future__ import annotations

from collections import deque
from typing import Deque, Tuple

from PySide6.QtWidgets import QVBoxLayout, QWidget
import pyqtgraph as pg


class ChartWidget(QWidget):
    """Plot widget with double-buffered data ingestion."""

    def __init__(self, title: str, max_points: int = 1000) -> None:
        super().__init__()
        self.max_points = max_points
        self.buffer_a: Deque[Tuple[float, float]] = deque()
        self.buffer_b: Deque[Tuple[float, float]] = deque()
        self.x_data: Deque[float] = deque(maxlen=max_points)
        self.y_data: Deque[float] = deque(maxlen=max_points)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        self.plot = pg.PlotWidget(title=title)
        self.plot.showGrid(x=True, y=True, alpha=0.25)
        self.curve = self.plot.plot(pen=pg.mkPen(width=2))
        layout.addWidget(self.plot)

    def push_point(self, ts: float, value: float) -> None:
        """Append data into the ingress buffer from any thread."""
        self.buffer_a.append((ts, value))

    def swap_buffers(self) -> None:
        """Swap ingress/egress buffers (call on UI thread)."""
        self.buffer_a, self.buffer_b = self.buffer_b, self.buffer_a

    def update_chart(self) -> None:
        """Flush buffer_b to the curve."""
        if not self.buffer_b:
            return
        while self.buffer_b:
            ts, val = self.buffer_b.popleft()
            self.x_data.append(ts)
            self.y_data.append(val)
        self.curve.setData(list(self.x_data), list(self.y_data))
