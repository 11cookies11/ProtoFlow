from __future__ import annotations

from typing import Iterable, List

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QWidget, QVBoxLayout

from ui.charts.chart_widget import ChartWidget


class ScriptWindow(QMainWindow):
    """Window hosting one or more ChartWidget, refreshed by its own timer."""

    def __init__(self, title: str, charts: Iterable[ChartWidget], interval_ms: int = 30, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.charts: List[ChartWidget] = list(charts)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        for chart in self.charts:
            layout.addWidget(chart)

        self.status_label = QLabel("Updating…")
        self.status_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(self.status_label)

        self.setCentralWidget(container)

        self.timer = QTimer(self)
        self.timer.setInterval(interval_ms)
        self.timer.timeout.connect(self._tick)
        self.timer.start()

    def _tick(self) -> None:
        for chart in self.charts:
            chart.swap_buffers()
            chart.update_chart()

    def closeEvent(self, event) -> None:  # pragma: no cover - UI event
        if self.timer.isActive():
            self.timer.stop()
        super().closeEvent(event)
