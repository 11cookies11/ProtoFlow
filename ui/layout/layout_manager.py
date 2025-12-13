from __future__ import annotations

from typing import Dict, Iterable, List, Optional

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QMainWindow, QSplitter, QVBoxLayout, QWidget, QLabel
except ImportError:  # pragma: no cover
    from PyQt6.QtCore import Qt  # type: ignore
    from PyQt6.QtWidgets import QMainWindow, QSplitter, QVBoxLayout, QWidget, QLabel  # type: ignore

from dsl.ast_nodes import ChartSpec, ControlSpec, LayoutNode
from ui.charts.chart_widget import ChartWidget
from ui.controls.control_window import ControlWidget


class LayoutWindow(QMainWindow):
    """Single window hosting a layout tree of charts/controls."""

    def __init__(self, root_widget: QWidget, title: str = "Layout") -> None:
        super().__init__()
        self.setWindowTitle(title)
        self.setCentralWidget(root_widget)


class LayoutManager:
    """Builds layout tree into a single window and routes chart data."""

    def __init__(
        self,
        root: LayoutNode,
        chart_specs: Iterable[ChartSpec],
        control_specs: Iterable[ControlSpec],
        bus=None,
        title: str = "Layout",
    ) -> None:
        self.root = root
        self.bus = bus
        self.chart_specs = {c.id: c for c in chart_specs}
        self.control_specs = {c.id: c for c in control_specs}
        self.chart_widgets: Dict[str, ChartWidget] = {}
        self.control_widgets: Dict[str, ControlWidget] = {}
        self.bind_map: Dict[str, List[ChartWidget]] = {}

        root_widget = self._build_widget(root)
        self.window = LayoutWindow(root_widget, title=title)
        self.window.show()

    def _build_widget(self, node: LayoutNode) -> QWidget:
        if node.type == "split":
            orientation = Qt.Horizontal if (node.orientation or "horizontal") == "horizontal" else Qt.Vertical
            splitter = QSplitter(orientation)
            for child in node.children:
                splitter.addWidget(self._build_widget(child))
            return splitter

        # Leaf: create a container with the requested widgets
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        for cid in node.charts:
            spec = self.chart_specs.get(cid)
            if not spec:
                layout.addWidget(QLabel(f"Unknown chart: {cid}"))
                continue
            widget = ChartWidget(title=spec.title, max_points=spec.max_points)
            self.chart_widgets[cid] = widget
            self.bind_map.setdefault(spec.bind, []).append(widget)
            layout.addWidget(widget)

        for ctrl_id in node.controls:
            spec = self.control_specs.get(ctrl_id)
            if not spec:
                layout.addWidget(QLabel(f"Unknown control: {ctrl_id}"))
                continue
            widget = ControlWidget(spec, self.bus)
            self.control_widgets[ctrl_id] = widget
            layout.addWidget(widget)

        if not node.charts and not node.controls:
            layout.addWidget(QLabel("Empty leaf"))
        return container

    def handle_data(self, payload: Dict[str, float]) -> None:
        """Route incoming data to chart widgets."""
        ts = float(payload.get("ts", 0))
        for key, value in payload.items():
            if key == "ts":
                continue
            widgets = self.bind_map.get(key)
            if not widgets:
                continue
            try:
                val_f = float(value)
            except Exception:
                continue
            for w in widgets:
                w.push_point(ts, val_f)

    def close_all(self) -> None:
        try:
            self.window.close()
        except Exception:
            pass
