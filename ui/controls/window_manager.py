from __future__ import annotations

from typing import Iterable, List

from PySide6.QtCore import QObject

from dsl.ast_nodes import ControlSpec
from ui.controls.control_window import ControlWindow


class ControlWindowManager(QObject):
    """Create and manage non-modal control windows."""

    def __init__(self, specs: Iterable[ControlSpec], bus, parent=None) -> None:
        super().__init__(parent)
        self.specs = list(specs)
        self.bus = bus
        self.windows: List[ControlWindow] = []
        self._build()

    def _build(self) -> None:
        for spec in self.specs:
            win = ControlWindow(spec, self.bus)
            self.windows.append(win)
            win.show()

    def close_all(self) -> None:
        for win in self.windows:
            try:
                win.close()
            except Exception:
                pass
        self.windows.clear()

