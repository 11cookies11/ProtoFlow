from __future__ import annotations

from pathlib import Path

try:
    from PySide6.QtCore import QUrl
    from PySide6.QtWebChannel import QWebChannel
    from PySide6.QtWidgets import QMainWindow
    from PySide6.QtWebEngineWidgets import QWebEngineView
except ImportError:  # pragma: no cover
    from PyQt6.QtCore import QUrl  # type: ignore
    from PyQt6.QtWebChannel import QWebChannel  # type: ignore
    from PyQt6.QtWidgets import QMainWindow  # type: ignore
    from PyQt6.QtWebEngineWidgets import QWebEngineView  # type: ignore

from ui.web_bridge import WebBridge

class WebWindow(QMainWindow):
    """Minimal WebEngine host window for the new web UI."""

    def __init__(self, bus=None, comm=None) -> None:
        super().__init__()
        self.setWindowTitle("ProtoFlow Web UI")
        self.resize(1200, 800)

        view = QWebEngineView(self)
        self.setCentralWidget(view)

        channel = QWebChannel(view)
        self.bridge = WebBridge(bus=bus, comm=comm)
        channel.registerObject("bridge", self.bridge)
        view.page().setWebChannel(channel)

        repo_root = Path(__file__).resolve().parents[1]
        dist_index = repo_root / "web-ui" / "dist" / "index.html"
        fallback_index = repo_root / "assets" / "web" / "index.html"
        index_path = dist_index if dist_index.exists() else fallback_index
        view.load(QUrl.fromLocalFile(str(index_path)))
