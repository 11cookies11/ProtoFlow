from __future__ import annotations

from pathlib import Path
import ctypes
import logging
import os
import sys

try:
    from PySide6.QtCore import QEvent, QPoint, QTimer, Qt, QUrl
    from PySide6.QtGui import QAction, QGuiApplication, QIcon
    from PySide6.QtWebChannel import QWebChannel
    from PySide6.QtWebEngineCore import QWebEnginePage
    from PySide6.QtWidgets import QFileDialog, QMainWindow, QMenu
    from PySide6.QtWebEngineWidgets import QWebEngineView
except ImportError:  # pragma: no cover
    from PyQt6.QtCore import QEvent, QPoint, QTimer, Qt, QUrl  # type: ignore
    from PyQt6.QtGui import QAction, QGuiApplication, QIcon  # type: ignore
    from PyQt6.QtWebChannel import QWebChannel  # type: ignore
    from PyQt6.QtWebEngineCore import QWebEnginePage  # type: ignore
    from PyQt6.QtWidgets import QFileDialog, QMainWindow, QMenu  # type: ignore
    from PyQt6.QtWebEngineWidgets import QWebEngineView  # type: ignore

from ui.desktop.web_bridge import WebBridge
from ui.desktop.win_snap import apply_snap_styles

if sys.platform == "win32":
    WM_NCHITTEST = 0x0084
    HTCAPTION = 2

    class MSG(ctypes.Structure):
        _fields_ = [
            ("hwnd", ctypes.c_void_p),
            ("message", ctypes.c_uint),
            ("wParam", ctypes.c_size_t),
            ("lParam", ctypes.c_ssize_t),
            ("time", ctypes.c_uint),
            ("pt_x", ctypes.c_long),
            ("pt_y", ctypes.c_long),
            ("lPrivate", ctypes.c_uint),
        ]

class LoggingWebPage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, line_number, source_id):  # type: ignore[override]
        level_map = {
            QWebEnginePage.JavaScriptConsoleMessageLevel.InfoMessageLevel: "INFO",
            QWebEnginePage.JavaScriptConsoleMessageLevel.WarningMessageLevel: "WARN",
            QWebEnginePage.JavaScriptConsoleMessageLevel.ErrorMessageLevel: "ERROR",
        }
        tag = level_map.get(level, "LOG")
        logging.getLogger("web_js").warning(
            "[%s] %s (%s:%s)",
            tag,
            message,
            source_id,
            line_number,
        )
        super().javaScriptConsoleMessage(level, message, line_number, source_id)

class WebWindow(QMainWindow):
    """Minimal WebEngine host window for the new web UI."""

    def __init__(
        self,
        bus=None,
        comm=None,
        plugin_manager=None,
        proxy_manager=None,
        proxy_monitor_enabled: bool = True,
    ) -> None:
        super().__init__()
        self.setWindowTitle("ProtoFlow Web UI")
        self._apply_initial_geometry()
        self._normal_geometry = self.geometry()
        self._titlebar_height = 36
        self._win_style_applied = False
        # Stable default: manual snap fallback enabled.
        # Set PROTOFLOW_NATIVE_CAPTION=1 to opt into the native caption experiment.
        self._native_caption_enabled = sys.platform == "win32" and os.environ.get("PROTOFLOW_NATIVE_CAPTION", "0") == "1"

        self.setMinimumSize(960, 600)
        self.setWindowFlags(
            Qt.Window | Qt.FramelessWindowHint | Qt.WindowSystemMenuHint | Qt.WindowMinMaxButtonsHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        view = QWebEngineView(self)
        page = LoggingWebPage(view)
        view.setPage(page)
        self._view = view
        self._stabilize_pending = False
        self.setCentralWidget(view)

        channel = QWebChannel(view)
        self.bridge = WebBridge(
            bus=bus,
            comm=comm,
            window=self,
            proxy_manager=proxy_manager,
            proxy_monitor_enabled=proxy_monitor_enabled,
        )
        channel.registerObject("bridge", self.bridge)
        view.page().setWebChannel(channel)

        resource_root = self._resolve_resource_root()
        icon_ico = self._find_existing_path(
            resource_root.parent / "installer" / "ProtoFlow.ico",
            resource_root / "installer" / "ProtoFlow.ico",
            resource_root / "assets" / "icons" / "ProtoFlow.ico",
            resource_root / "ui" / "assets" / "icons" / "ProtoFlow.ico",
        )
        icon_svg = self._find_existing_path(
            resource_root / "assets" / "icons" / "logo_mark.svg",
            resource_root / "ui" / "assets" / "icons" / "logo_mark.svg",
            resource_root / "assets" / "icons" / "logo.svg",
            resource_root / "ui" / "assets" / "icons" / "logo.svg",
        )
        icon_png = self._find_existing_path(
            resource_root / "assets" / "icons" / "logo_mark.png",
            resource_root / "ui" / "assets" / "icons" / "logo_mark.png",
            resource_root / "assets" / "icons" / "logo.png",
            resource_root / "ui" / "assets" / "icons" / "logo.png",
        )
        icon = QIcon(str(icon_ico))
        if icon.isNull():
            icon = QIcon(str(icon_svg))
        if icon.isNull():
            icon = QIcon(str(icon_png))
        if not icon.isNull():
            self.setWindowIcon(icon)
        index_path = self._find_existing_path(
            resource_root / "frontend" / "dist" / "index.html",
            resource_root / "ui" / "frontend" / "dist" / "index.html",
            resource_root / "assets" / "web" / "index.html",
            resource_root / "ui" / "assets" / "web" / "index.html",
        )
        view.load(QUrl.fromLocalFile(str(index_path)))
        view.page().profile().downloadRequested.connect(self._handle_download)

    def _apply_initial_geometry(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if not screen:
            self.resize(1200, 800)
            return
        rect = screen.availableGeometry()
        target_w = max(960, min(int(rect.width() * 0.9), rect.width()))
        target_h = max(600, min(int(rect.height() * 0.9), rect.height()))
        self.resize(target_w, target_h)
        self.move(rect.x() + (rect.width() - target_w) // 2, rect.y() + (rect.height() - target_h) // 2)

    def nativeEvent(self, event_type, message):  # type: ignore[override]
        if not self._native_caption_enabled:
            return super().nativeEvent(event_type, message)
        try:
            msg = MSG.from_address(int(message))
        except Exception:
            return super().nativeEvent(event_type, message)
        if msg.message != WM_NCHITTEST:
            return super().nativeEvent(event_type, message)
        hit = self._hit_test_native_caption(msg.lParam)
        if hit is None:
            return False, 0
        return True, hit

    def _hit_test_native_caption(self, l_param: int):
        # lParam packs signed x/y screen coordinates.
        x = ctypes.c_short(l_param & 0xFFFF).value
        y = ctypes.c_short((l_param >> 16) & 0xFFFF).value
        local = self.mapFromGlobal(QPoint(x, y))
        lx = local.x()
        ly = local.y()
        width = self.width()
        height = self.height()
        if lx < 0 or ly < 0 or lx >= width or ly >= height:
            return None
        if not (0 <= ly < self._titlebar_height):
            return None
        # Gray rollout: only expose a narrow center band as native caption.
        band = max(220, int(width * 0.28))
        start = (width - band) // 2
        end = start + band
        if start <= lx < end:
            return HTCAPTION
        return None

    @staticmethod
    def _find_existing_path(*candidates: Path) -> Path:
        for path in candidates:
            if path.exists():
                return path
        return candidates[0]

    def _resolve_resource_root(self) -> Path:
        source_ui_dir = Path(__file__).resolve().parents[1]
        if not getattr(sys, "frozen", False):
            return source_ui_dir

        candidates = []
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidates.append(Path(meipass))
            candidates.append(Path(meipass) / "ui")

        exe_dir = Path(sys.executable).resolve().parent
        candidates.append(exe_dir)
        candidates.append(exe_dir / "_internal")
        candidates.append(exe_dir / "ui")

        for root in candidates:
            if (root / "frontend" / "dist" / "index.html").exists():
                return root
            if (root / "ui" / "frontend" / "dist" / "index.html").exists():
                return root
            if (root / "assets" / "web" / "index.html").exists():
                return root
            if (root / "ui" / "assets" / "web" / "index.html").exists():
                return root
        return candidates[0] if candidates else source_ui_dir

    def _handle_download(self, item) -> None:
        suggested = item.downloadFileName()
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save log",
            suggested or "io_logs.log",
            "Log Files (*.log);;All Files (*.*)",
        )
        if not path:
            item.cancel()
            return
        directory = os.path.dirname(path)
        filename = os.path.basename(path)
        if hasattr(item, "setDownloadDirectory"):
            item.setDownloadDirectory(directory)
        if hasattr(item, "setDownloadFileName"):
            item.setDownloadFileName(filename)
        elif hasattr(item, "setPath"):
            item.setPath(path)
        item.accept()

    def _apply_snap(self, screen_x: int, screen_y: int) -> bool:
        if self._native_caption_enabled:
            return False
        screen = QGuiApplication.screenAt(QPoint(screen_x, screen_y))
        if not screen:
            screen = self.screen() if hasattr(self, "screen") else None
        if not screen:
            return False
        rect = screen.availableGeometry()
        margin = 16
        at_left = screen_x <= rect.x() + margin
        at_right = screen_x >= rect.x() + rect.width() - margin
        at_top = screen_y <= rect.y() + margin
        if not (at_left or at_right or at_top):
            return False
        self.showNormal()
        if at_top and not (at_left or at_right):
            self._remember_normal_geometry()
            self.showMaximized()
            self._stabilize_webview_after_resize()
            return True
        if at_top and at_left:
            self.setGeometry(rect.x(), rect.y(), rect.width() // 2, rect.height() // 2)
        elif at_top and at_right:
            self.setGeometry(
                rect.x() + rect.width() // 2,
                rect.y(),
                rect.width() // 2,
                rect.height() // 2,
            )
        elif at_left:
            self.setGeometry(rect.x(), rect.y(), rect.width() // 2, rect.height())
        elif at_right:
            self.setGeometry(rect.x() + rect.width() // 2, rect.y(), rect.width() // 2, rect.height())
        else:
            self._remember_normal_geometry()
            self.setGeometry(rect)
        self._stabilize_webview_after_resize()
        return True

    def _start_move(self, screen_x: int, screen_y: int) -> None:
        handle = self.windowHandle()
        if self.isMaximized():
            screen = QGuiApplication.screenAt(QPoint(screen_x, screen_y))
            if not screen:
                screen = self.screen() if hasattr(self, "screen") else None
            normal = self._get_normal_geometry()
            self.showNormal()
            self.setWindowState(self.windowState() & ~Qt.WindowMaximized)
            self.setGeometry(self.x(), self.y(), normal.width(), normal.height())
            self._stabilize_webview_after_resize()
        if handle and hasattr(handle, "startSystemMove"):
            handle.startSystemMove()

    def _show_system_menu(self, screen_x: int, screen_y: int) -> None:
        menu = QMenu(self)
        action_restore = QAction("Restore", self)
        action_move = QAction("Move", self)
        action_size = QAction("Size", self)
        action_min = QAction("Minimize", self)
        action_max = QAction("Maximize", self)
        action_close = QAction("Close", self)

        action_restore.setEnabled(self.isMaximized() or self.isMinimized())
        action_max.setEnabled(not self.isMaximized())
        action_min.setEnabled(not self.isMinimized())

        action_restore.triggered.connect(self.showNormal)
        action_min.triggered.connect(self.showMinimized)
        action_max.triggered.connect(self.showMaximized)
        action_close.triggered.connect(self.close)

        def _move_window() -> None:
            handle = self.windowHandle()
            if handle and hasattr(handle, "startSystemMove"):
                handle.startSystemMove()

        def _resize_window() -> None:
            handle = self.windowHandle()
            if handle and hasattr(handle, "startSystemResize"):
                handle.startSystemResize(Qt.BottomEdge | Qt.RightEdge)

        action_move.triggered.connect(_move_window)
        action_size.triggered.connect(_resize_window)

        menu.addAction(action_restore)
        menu.addSeparator()
        menu.addAction(action_move)
        menu.addAction(action_size)
        menu.addSeparator()
        menu.addAction(action_min)
        menu.addAction(action_max)
        menu.addSeparator()
        menu.addAction(action_close)

        menu.exec(QPoint(screen_x, screen_y))

    def _start_resize(self, edge: str) -> None:
        handle = self.windowHandle()
        if not handle or not hasattr(handle, "startSystemResize"):
            return
        resize_edges = {
            "left": Qt.LeftEdge,
            "right": Qt.RightEdge,
            "top": Qt.TopEdge,
            "bottom": Qt.BottomEdge,
            "top-left": Qt.TopEdge | Qt.LeftEdge,
            "top-right": Qt.TopEdge | Qt.RightEdge,
            "bottom-left": Qt.BottomEdge | Qt.LeftEdge,
            "bottom-right": Qt.BottomEdge | Qt.RightEdge,
        }
        edge_flag = resize_edges.get(edge)
        if not edge_flag:
            return
        handle.startSystemResize(edge_flag)

    def _remember_normal_geometry(self) -> None:
        self._normal_geometry = self.geometry()

    def _get_normal_geometry(self):
        return self._normal_geometry

    def _toggle_max_restore(self) -> None:
        if self.isMaximized():
            self.showNormal()
        else:
            self._remember_normal_geometry()
            self.showMaximized()
        self._stabilize_webview_after_resize()

    def _stabilize_webview_after_resize(self) -> None:
        if self._stabilize_pending:
            return
        self._stabilize_pending = True

        def _refresh():
            self._stabilize_pending = False
            view = getattr(self, "_view", None)
            if view is None:
                return
            # Avoid aggressive forced repaint that can flash after drag/resize on Windows.
            view.resize(self.centralWidget().size())
            view.update()

        QTimer.singleShot(0, _refresh)

    def changeEvent(self, event):  # type: ignore[override]
        super().changeEvent(event)
        if event.type() == QEvent.WindowStateChange:
            self._stabilize_webview_after_resize()

    def _mouse_pos(self, event) -> QPoint:
        pos = event.globalPosition().toPoint()
        return pos

    def _handle_mouse_press(self, event) -> None:
        if event.button() == Qt.LeftButton:
            pos = self._mouse_pos(event)
            widget = self.childAt(event.position().toPoint())
            if widget and widget.property("resize-edge"):
                self._start_resize(widget.property("resize-edge"))
                return
            if self._is_titlebar_area(pos.x(), pos.y()):
                self._start_move(pos.x(), pos.y())
                return
        if event.button() == Qt.RightButton:
            pos = self._mouse_pos(event)
            if self._is_titlebar_area(pos.x(), pos.y()):
                self._show_system_menu(pos.x(), pos.y())
                return

    def _handle_mouse_double_click(self, event) -> None:
        if self._is_titlebar_area(event.position().toPoint().x(), event.position().toPoint().y()):
            self._toggle_max_restore()

    def _handle_mouse_move(self, event) -> None:
        if event.buttons() & Qt.LeftButton:
            return
        pos = event.position().toPoint()
        widget = self.childAt(pos)
        if widget and widget.property("resize-edge"):
            edge = widget.property("resize-edge")
            cursor_map = {
                "left": Qt.SizeHorCursor,
                "right": Qt.SizeHorCursor,
                "top": Qt.SizeVerCursor,
                "bottom": Qt.SizeVerCursor,
                "top-left": Qt.SizeFDiagCursor,
                "bottom-right": Qt.SizeFDiagCursor,
                "top-right": Qt.SizeBDiagCursor,
                "bottom-left": Qt.SizeBDiagCursor,
            }
            cursor = cursor_map.get(edge, Qt.ArrowCursor)
            self.setCursor(cursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def _handle_mouse_leave(self, event) -> None:
        self.setCursor(Qt.ArrowCursor)

    def _bind_titlebar_events(self):
        if hasattr(self, "title_bar"):
            self.title_bar.mousePressEvent = self._handle_mouse_press
            self.title_bar.mouseDoubleClickEvent = self._handle_mouse_double_click
            self.title_bar.mouseMoveEvent = self._handle_mouse_move
            self.title_bar.leaveEvent = self._handle_mouse_leave

    def _is_titlebar_area(self, screen_x: int, screen_y: int) -> bool:
        if self.isMaximized():
            return screen_y <= self._titlebar_height
        frame_y = self.y()
        if self._win_style_applied:
            frame_y += self._titlebar_height
        return screen_y <= frame_y + self._titlebar_height

    def _apply_custom_titlebar(self) -> None:
        resource_root = self._resolve_resource_root()
        style_path = self._find_existing_path(
            resource_root / "assets" / "styles" / "window.css",
            resource_root / "ui" / "assets" / "styles" / "window.css",
        )
        if not style_path.exists():
            return
        self.setStyleSheet(style_path.read_text(encoding="utf-8"))
        apply_snap_styles(self)
        self._win_style_applied = True

    def _init_system_titlebar(self):
        resource_root = self._resolve_resource_root()
        html_path = self._find_existing_path(
            resource_root / "assets" / "titlebar" / "titlebar.html",
            resource_root / "ui" / "assets" / "titlebar" / "titlebar.html",
        )
        if not html_path.exists():
            return
        html = html_path.read_text(encoding="utf-8")
        view = QWebEngineView(self)
        view.setObjectName("title_bar")
        view.setFixedHeight(self._titlebar_height)
        view.setContextMenuPolicy(Qt.NoContextMenu)
        view.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        view.load(QUrl.fromLocalFile(str(html_path)))
        view.page().setBackgroundColor(Qt.transparent)
        view.setStyleSheet("background: transparent")
        view.page().setHtml(html)
        view.setParent(self)
        view.show()
        self.title_bar = view
        self._bind_titlebar_events()

    def _init_titlebar(self):
        if sys.platform == "darwin":
            self._init_system_titlebar()
        else:
            self._apply_custom_titlebar()

    def showEvent(self, event):
        super().showEvent(event)
        self._init_titlebar()
