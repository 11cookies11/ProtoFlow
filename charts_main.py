from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from runtime.chart_runtime import ChartRuntime
from ui.charts.ui_builder import charts_from_yaml
from ui.charts.window_manager import WindowManager


def main(script_path: str | None = None) -> int:
    app = QApplication.instance() or QApplication(sys.argv)

    path = Path(script_path or "charts_example.yaml")
    charts = charts_from_yaml(path)
    if not charts:
        print("No charts defined in YAML ui.charts")
        return 1

    manager = WindowManager(charts)
    keys = {c.bind for c in charts}
    runtime = ChartRuntime(keys)
    runtime.data_ready.connect(manager.handle_data)
    runtime.start()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
