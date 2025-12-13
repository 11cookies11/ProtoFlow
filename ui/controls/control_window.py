from __future__ import annotations

from typing import Dict, List, Tuple

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QDoubleSpinBox,
        QFormLayout,
        QHBoxLayout,
        QLabel,
        QMainWindow,
        QPushButton,
        QLineEdit,
        QSlider,
        QSpinBox,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # pragma: no cover
    from PyQt6.QtCore import Qt  # type: ignore
    from PyQt6.QtWidgets import (  # type: ignore
        QCheckBox,
        QComboBox,
        QDoubleSpinBox,
        QFormLayout,
        QHBoxLayout,
        QLabel,
        QMainWindow,
        QPushButton,
        QLineEdit,
        QSlider,
        QSpinBox,
        QVBoxLayout,
        QWidget,
    )

from dsl.ast_nodes import ControlActionSpec, ControlInputSpec, ControlSpec


class _InputAdapter:
    """Helper to read/set values consistently."""

    def __init__(self, widget, spec: ControlInputSpec, scale: float = 1.0) -> None:
        self.widget = widget
        self.spec = spec
        self.scale = scale

    def value(self):
        if isinstance(self.widget, QCheckBox):
            return bool(self.widget.isChecked())
        if isinstance(self.widget, QComboBox):
            return self.widget.currentText()
        if hasattr(self.widget, "text"):
            return self.widget.text()
        if isinstance(self.widget, (QSpinBox, QDoubleSpinBox)):
            return float(self.widget.value()) if self.spec.itype == "float" else int(self.widget.value())
        if isinstance(self.widget, QSlider):
            raw = self.widget.value() / self.scale
            return float(raw) if self.spec.itype == "float" else int(raw)
        return None


class ControlWindow(QMainWindow):
    """Non-modal control window that emits EventBus events on action buttons."""

    def __init__(self, spec: ControlSpec, bus) -> None:
        super().__init__()
        self.spec = spec
        self.bus = bus
        self.setWindowTitle(spec.title)
        self.inputs: Dict[str, _InputAdapter] = {}
        self._build_ui(spec.inputs, spec.actions)

    def _build_ui(self, inputs: List[ControlInputSpec], actions: List[ControlActionSpec]) -> None:
        form = QFormLayout()
        for inp in inputs:
            widget, adapter = self._create_input_widget(inp)
            self.inputs[inp.name] = adapter
            form.addRow(QLabel(inp.label), widget)

        action_row = QHBoxLayout()
        action_row.addStretch()
        self._action_emit_map: List[Tuple[str, str]] = []
        for act in actions:
            btn = QPushButton(act.label or act.name)
            btn.clicked.connect(lambda _=False, emit=act.emit: self._emit_action(emit))
            action_row.addWidget(btn)
            self._action_emit_map.append((act.name, act.emit))

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addLayout(form)
        layout.addLayout(action_row)
        layout.addStretch()
        self.setCentralWidget(container)

    def _create_input_widget(self, spec: ControlInputSpec) -> tuple[QWidget, _InputAdapter]:
        itype = spec.itype
        minimum = spec.minimum if spec.minimum is not None else 0
        maximum = spec.maximum if spec.maximum is not None else (1 if itype == "bool" else 100)
        step = spec.step if spec.step is not None else (0.1 if itype == "float" else 1)

        if itype in {"text", "string", "field"}:
            line = QLineEdit()
            if spec.placeholder:
                line.setPlaceholderText(str(spec.placeholder))
            if spec.default is not None:
                line.setText(str(spec.default))
            return line, _InputAdapter(line, spec)

        if itype == "bool":
            cb = QCheckBox()
            cb.setChecked(bool(spec.default) if spec.default is not None else False)
            return cb, _InputAdapter(cb, spec)

        if itype == "select":
            combo = QComboBox()
            for opt in spec.options:
                combo.addItem(str(opt))
            if spec.default and str(spec.default) in spec.options:
                combo.setCurrentText(str(spec.default))
            return combo, _InputAdapter(combo, spec)

        # Number inputs: slider + spin
        scale = 1.0
        if itype == "float":
            # Use slider with scaling to preserve decimals
            factor = max(1, int(round(1 / step))) if step else 10
            scale = float(factor)
            slider = QSlider(Qt.Horizontal)
            slider.setMinimum(int(minimum * factor))
            slider.setMaximum(int(maximum * factor))
            slider.setSingleStep(int(step * factor))

            spin = QDoubleSpinBox()
            spin.setRange(float(minimum), float(maximum))
            spin.setSingleStep(float(step))
            spin.setDecimals(4)
            if spec.default is not None:
                spin.setValue(float(spec.default))
                slider.setValue(int(float(spec.default) * factor))

            slider.valueChanged.connect(lambda v: spin.setValue(v / factor))
            spin.valueChanged.connect(lambda v: slider.setValue(int(v * factor)))

            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.addWidget(slider, 2)
            row_layout.addWidget(spin, 1)
            return row, _InputAdapter(slider, spec, scale=factor)

        # int (default)
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(int(minimum))
        slider.setMaximum(int(maximum))
        slider.setSingleStep(int(step))

        spin = QSpinBox()
        spin.setRange(int(minimum), int(maximum))
        spin.setSingleStep(int(step))
        if spec.default is not None:
            spin.setValue(int(spec.default))
            slider.setValue(int(spec.default))

        slider.valueChanged.connect(spin.setValue)
        spin.valueChanged.connect(slider.setValue)

        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.addWidget(slider, 2)
        row_layout.addWidget(spin, 1)
        return row, _InputAdapter(slider, spec)

    def _emit_action(self, emit_name: str) -> None:
        payload = {name: adapter.value() for name, adapter in self.inputs.items()}
        if self.bus:
            try:
                self.bus.publish(emit_name, payload)
            except Exception:
                pass
