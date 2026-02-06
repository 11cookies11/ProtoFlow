from __future__ import annotations

import importlib
import json
import pkgutil
import re
import threading
import time
from pathlib import Path
import logging
import os
from typing import Any, Dict, List, Optional
import yaml

try:
    from PySide6.QtCore import QObject, Q_ARG, QMetaObject, QTimer, Qt, Signal, Slot
    from PySide6.QtWidgets import QFileDialog
except ImportError:  # pragma: no cover
    from PyQt6.QtCore import QObject, Q_ARG, QMetaObject, QTimer, Qt, pyqtSignal as Signal, pyqtSlot as Slot  # type: ignore
    from PyQt6.QtWidgets import QFileDialog  # type: ignore

from infra.protocol.registry import ProtocolRegistry
import infra.protocol as protocols_pkg
from desktop.script_runner_qt import ScriptRunnerQt


class WebBridge(QObject):
    """QWebChannel bridge for Web UI."""

    log = Signal(str)
    ui_ready = Signal()
    comm_rx = Signal(str)
    comm_tx = Signal(str)
    comm_status = Signal(object)
    protocol_frame = Signal(object)
    capture_frame = Signal(object)
    comm_batch = Signal(str)
    script_log = Signal(str)
    script_state = Signal(str)
    script_progress = Signal(int)
    channel_update = Signal(object)
    ui_event_log = Signal(object)

    def __init__(self, bus=None, comm=None, window=None) -> None:
        super().__init__()
        self._logger = logging.getLogger("web_bridge")
        self._bus = bus
        self._comm = comm
        self._window = window
        self._script_runner: Optional[ScriptRunnerQt] = None
        self._buffer: List[Dict[str, Any]] = []
        self._protocols_loaded = False
        self._settings_root = Path(os.environ.get("LOCALAPPDATA", Path.cwd())) / "ProtoFlow"
        self._settings_path = self._settings_root / "config" / "ui_settings.json"
        self._proxy_pairs_path = self._settings_root / "config" / "proxy_pairs.json"
        self._protocols_path = self._settings_root / "config" / "protocols.json"
        self._proxy_pairs: List[Dict[str, Any]] = self._load_proxy_pairs()
        self._custom_protocols: List[Dict[str, Any]] = self._load_custom_protocols()
        self._channel_state: Dict[str, Any] = {
            "type": None,
            "status": "disconnected",
            "port": None,
            "baud": None,
            "host": None,
            "address": None,
            "error": None,
        }
        self._traffic: Dict[str, int] = {"tx": 0, "rx": 0}
        self._last_channel_emit = 0.0
        self._connect_lock = threading.Lock()
        self._connect_inflight = False
        self._last_status_ts = 0.0
        self._last_error: Optional[str] = None
        self._last_error_ts = 0.0
        self._manual_disconnect = False
        self._flush_timer = QTimer(self)
        self._flush_timer.setInterval(50)
        self._flush_timer.timeout.connect(self._flush_buffers)
        self._flush_timer.start()
        if self._bus:
            self._bus.subscribe("comm.rx", self._on_comm_rx)
            self._bus.subscribe("comm.tx", self._on_comm_tx)
            self._bus.subscribe("comm.connected", self._on_comm_status)
            self._bus.subscribe("comm.disconnected", self._on_comm_status)
            self._bus.subscribe("comm.error", self._on_comm_status)
            self._bus.subscribe("protocol.frame", self._on_protocol_frame)
            self._bus.subscribe("capture.frame", self._on_capture_frame)

    def _read_app_version(self) -> str:
        env_version = os.environ.get("PROTOFLOW_VERSION")
        if env_version:
            return env_version.strip()
        try:
            version_path = Path(__file__).resolve().parents[1] / "VERSION"
            if version_path.is_file():
                return version_path.read_text(encoding="utf-8").strip()
        except Exception:
            return "v0.0.0"
        return "v0.0.0"

    @Slot(result=str)
    def get_app_version(self) -> str:
        return self._read_app_version()

    @Slot(str, result=str)
    def ping(self, message: str) -> str:
        return f"pong: {message}"

    @Slot()
    def notify_ready(self) -> None:
        self.ui_ready.emit()

    @Slot(result="QVariant")
    def list_ports(self) -> list[str]:
        if not self._comm:
            return []
        return self._comm.list_serial_ports()

    @Slot(result="QVariant")
    def list_channels(self) -> List[Dict[str, Any]]:
        return self._build_channel_list()

    @Slot(result="QVariant")
    def list_protocols(self) -> List[Dict[str, Any]]:
        self._load_protocols()
        registry = ProtocolRegistry.list()
        items: List[Dict[str, Any]] = []
        for key, cls in sorted(registry.items()):
            doc = (cls.__doc__ or "").strip()
            desc = doc.splitlines()[0].strip() if doc else ""
            category = self._protocol_category(key)
            items.append(
                {
                    "id": key,
                    "key": key,
                    "driver": cls.__name__,
                    "desc": desc,
                    "category": category,
                    "status": "available",
                    "source": "builtin",
                }
            )
        existing = {item.get("id") for item in items}
        for custom in self._custom_protocols:
            if not isinstance(custom, dict):
                continue
            custom_id = custom.get("id") or custom.get("key")
            if not custom_id or custom_id in existing:
                continue
            merged = {
                "id": custom_id,
                "key": custom.get("key") or custom_id,
                "name": custom.get("name") or "",
                "driver": custom.get("driver") or "",
                "desc": custom.get("desc") or "",
                "category": custom.get("category") or "custom",
                "status": custom.get("status") or "custom",
                "source": "custom",
            }
            items.append(merged)
        return items

    @Slot(str, result="QVariant")
    def parse_ui_yaml(self, yaml_text: str) -> Dict[str, Any]:
        try:
            data = yaml.safe_load(yaml_text) if yaml_text else {}
            return {"ok": True, "value": data}
        except yaml.YAMLError as exc:
            error: Dict[str, Any] = {"message": str(exc)}
            mark = getattr(exc, "problem_mark", None)
            if mark is not None:
                error["line"] = getattr(mark, "line", None) + 1 if hasattr(mark, "line") else None
                error["column"] = getattr(mark, "column", None) + 1 if hasattr(mark, "column") else None
            return {"ok": False, "error": error}

    @Slot("QVariant")
    def dispatch_ui_event(self, payload: Dict[str, Any]) -> None:
        if not isinstance(payload, dict):
            return
        event = {
            "ts": payload.get("ts") or time.time(),
            "emit": payload.get("emit") or "",
            "payload": payload.get("payload"),
            "source": payload.get("source"),
        }
        # Bridge UI events into the shared EventBus so DSL can react.
        if self._bus:
            try:
                if event["emit"]:
                    self._bus.publish(str(event["emit"]), event["payload"])
                # Also publish a generic UI event for simpler subscriptions.
                self._bus.publish("ui.event", event)
            except Exception:
                pass
        self.ui_event_log.emit(event)

    @Slot("QVariant", result="QVariant")
    def create_protocol(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            return {}
        self._load_protocols()
        raw_key = payload.get("key") or payload.get("id") or payload.get("name") or "custom_protocol"
        key = self._normalize_protocol_key(str(raw_key))
        key = self._ensure_protocol_key_unique(key)
        item = {
            "id": key,
            "key": key,
            "name": payload.get("name") or key,
            "desc": payload.get("desc") or "",
            "category": payload.get("category") or "custom",
            "status": payload.get("status") or "custom",
            "driver": payload.get("driver") or "",
        }
        self._custom_protocols.append(item)
        self._save_custom_protocols()
        return item

    @Slot("QVariant", result="QVariant")
    def update_protocol(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            return {}
        protocol_id = payload.get("id") or payload.get("key")
        if not protocol_id:
            return {}
        updated: Dict[str, Any] = {}
        for item in self._custom_protocols:
            if item.get("id") == protocol_id or item.get("key") == protocol_id:
                item["name"] = payload.get("name") or item.get("name") or item.get("key") or ""
                item["desc"] = payload.get("desc") or ""
                item["category"] = payload.get("category") or item.get("category") or "custom"
                item["status"] = payload.get("status") or item.get("status") or "custom"
                if payload.get("driver"):
                    item["driver"] = payload.get("driver")
                updated = dict(item)
                break
        if updated:
            self._save_custom_protocols()
        return updated

    @Slot(str, result=bool)
    def delete_protocol(self, protocol_id: str) -> bool:
        if not protocol_id:
            return False
        before = len(self._custom_protocols)
        self._custom_protocols = [
            item
            for item in self._custom_protocols
            if item.get("id") != protocol_id and item.get("key") != protocol_id
        ]
        if len(self._custom_protocols) == before:
            return False
        self._save_custom_protocols()
        return True

    @Slot(result="QVariant")
    def load_settings(self) -> Dict[str, Any]:
        return self._load_settings()

    @Slot(result="QVariant")
    def list_proxy_pairs(self) -> List[Dict[str, Any]]:
        return list(self._proxy_pairs)

    @Slot(result="QVariant")
    def refresh_proxy_pairs(self) -> List[Dict[str, Any]]:
        self._proxy_pairs = self._load_proxy_pairs()
        return list(self._proxy_pairs)

    @Slot("QVariant", result="QVariant")
    def create_proxy_pair(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            return {}
        pair = {
            "id": payload.get("id") or f"proxy-{int(time.time() * 1000)}",
            "name": payload.get("name") or "未命名转发对",
            "hostPort": payload.get("hostPort") or "",
            "devicePort": payload.get("devicePort") or "",
            "baud": payload.get("baud") or "115200",
            "status": payload.get("status") or "stopped",
            "dataBits": payload.get("dataBits") or "8",
            "stopBits": payload.get("stopBits") or "1",
            "parity": payload.get("parity") or "none",
            "flowControl": payload.get("flowControl") or "none",
        }
        self._proxy_pairs.insert(0, pair)
        self._save_proxy_pairs()
        return pair

    @Slot("QVariant", result="QVariant")
    def update_proxy_pair(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            return {}
        pair_id = payload.get("id")
        if not pair_id:
            return {}
        for idx, pair in enumerate(self._proxy_pairs):
            if pair.get("id") == pair_id:
                updated = {
                    **pair,
                    **{
                        k: v
                        for k, v in payload.items()
                        if k
                        in {
                            "name",
                            "hostPort",
                            "devicePort",
                            "baud",
                            "status",
                            "dataBits",
                            "stopBits",
                            "parity",
                            "flowControl",
                        }
                    },
                }
                self._proxy_pairs[idx] = updated
                self._save_proxy_pairs()
                return updated
        return {}

    @Slot(str, result=bool)
    def delete_proxy_pair(self, pair_id: str) -> bool:
        if not pair_id:
            return False
        before = len(self._proxy_pairs)
        self._proxy_pairs = [pair for pair in self._proxy_pairs if pair.get("id") != pair_id]
        if len(self._proxy_pairs) != before:
            self._save_proxy_pairs()
            return True
        return False

    @Slot(str, bool, result="QVariant")
    def set_proxy_pair_status(self, pair_id: str, active: bool) -> Dict[str, Any]:
        status = "running" if active else "stopped"
        for idx, pair in enumerate(self._proxy_pairs):
            if pair.get("id") == pair_id:
                pair = dict(pair)
                pair["status"] = status
                self._proxy_pairs[idx] = pair
                self._save_proxy_pairs()
                return pair
        return {}

    @Slot("QVariant", result=bool)
    def save_settings(self, payload: Dict[str, Any]) -> bool:
        return self._save_settings(payload)

    @Slot("QVariant", result=bool)
    def start_capture(self, payload: Dict[str, Any]) -> bool:
        if not isinstance(payload, dict):
            return False
        channel = payload.get("channel") or payload.get("hostPort")
        pair_id = payload.get("id") or payload.get("pairId")
        self._bus.publish(
            "capture.control",
            {
                "action": "start",
                "channel": channel,
                "pair_id": pair_id,
            },
        )
        return True

    @Slot(result=bool)
    def stop_capture(self) -> bool:
        self._bus.publish("capture.control", {"action": "stop"})
        return True

    @Slot(str, str, result=str)
    def select_directory(self, title: str, start_dir: str) -> str:
        return QFileDialog.getExistingDirectory(None, title or "Select directory", start_dir or "")

    @Slot(str, int)
    def connect_serial(self, port: str, baud: int = 115200) -> None:
        if not self._comm:
            return
        if self._connect_inflight:
            return
        if not self._connect_lock.acquire(blocking=False):
            return
        self._connect_inflight = True

        def _run() -> None:
            try:
                self._comm.select_serial(port, baud)
            finally:
                self._connect_lock.release()

        threading.Thread(target=_run, daemon=True).start()

    @Slot(str, int)
    def connect_tcp(self, host: str, port: int) -> None:
        if not self._comm:
            return
        if self._connect_inflight:
            return
        if not self._connect_lock.acquire(blocking=False):
            return
        self._connect_inflight = True

        def _run() -> None:
            try:
                self._comm.select_tcp(host, port)
            finally:
                self._connect_lock.release()

        threading.Thread(target=_run, daemon=True).start()

    @Slot()
    def disconnect(self) -> None:
        if self._comm:
            self._manual_disconnect = True
            self._comm.close()

    @Slot(str)
    def send_text(self, text: str) -> None:
        if self._comm:
            self._comm.send(text.encode())

    @Slot(str)
    def send_hex(self, hex_text: str) -> None:
        if not self._comm:
            return
        try:
            data = bytes.fromhex(hex_text.replace(" ", ""))
        except ValueError:
            self.log.emit("invalid hex string")
            return
        self._comm.send(data)

    @Slot(str)
    def run_script(self, yaml_text: str) -> None:
        if self._script_runner and self._script_runner.isRunning():
            self._script_runner.stop()
            self._script_runner.wait(1000)
        # Subscribe to a generic UI event channel by default.
        runner = ScriptRunnerQt(yaml_text, bus=self._bus, external_events=["ui.event"])
        runner.sig_log.connect(self.script_log.emit)
        runner.sig_state.connect(self.script_state.emit)
        runner.sig_progress.connect(self.script_progress.emit)
        self._script_runner = runner
        runner.start()

    @Slot()
    def stop_script(self) -> None:
        if self._script_runner and self._script_runner.isRunning():
            self._script_runner.stop()

    @Slot(result="QVariant")
    def load_yaml(self) -> Dict[str, str]:
        path, _ = QFileDialog.getOpenFileName(
            None,
            "Select YAML file",
            str(Path.cwd()),
            "YAML Files (*.yaml *.yml)",
        )
        if not path:
            return {}
        try:
            text = Path(path).read_text(encoding="utf-8")
        except Exception as exc:  # pragma: no cover - UI dialog failure
            self.script_log.emit(f"[ERROR] Load YAML failed: {exc}")
            return {}
        return {"path": path, "name": Path(path).name, "text": text}

    @Slot(str, str, result="QVariant")
    def save_yaml(self, yaml_text: str, suggested_name: str = "workflow.yaml") -> Dict[str, str]:
        if not yaml_text.strip():
            self.script_log.emit("[WARN] YAML is empty, not saved.")
            return {}
        default_path = Path.cwd() / (suggested_name or "workflow.yaml")
        path, _ = QFileDialog.getSaveFileName(
            None,
            "Save YAML file",
            str(default_path),
            "YAML Files (*.yaml *.yml)",
        )
        if not path:
            return {}
        try:
            Path(path).write_text(yaml_text, encoding="utf-8")
        except Exception as exc:  # pragma: no cover - UI dialog failure
            self.script_log.emit(f"[ERROR] Save YAML failed: {exc}")
            return {}
        return {"path": path, "name": Path(path).name}

    @Slot()
    def window_minimize(self) -> None:
        if self._window:
            self._window.showMinimized()

    @Slot()
    def window_maximize(self) -> None:
        if self._window:
            if hasattr(self._window, "_remember_normal_geometry"):
                self._window._remember_normal_geometry()
            self._window.showMaximized()

    @Slot()
    def window_restore(self) -> None:
        if self._window:
            self._window.showNormal()

    @Slot()
    def window_toggle_maximize(self) -> None:
        if not self._window:
            return
        if self._window.isMaximized():
            self._window.showNormal()
        else:
            if hasattr(self._window, "_remember_normal_geometry"):
                self._window._remember_normal_geometry()
            self._window.showMaximized()

    @Slot()
    def window_close(self) -> None:
        if self._window:
            self._window.close()

    @Slot()
    def window_start_move(self) -> None:
        if not self._window:
            return
        handle = self._window.windowHandle()
        if handle and hasattr(handle, "startSystemMove"):
            handle.startSystemMove()

    @Slot(int, int)
    def window_start_move_at(self, screen_x: int, screen_y: int) -> None:
        if not self._window:
            return
        if hasattr(self._window, "_start_move"):
            self._window._start_move(screen_x, screen_y)
            return
        handle = self._window.windowHandle()
        if handle and hasattr(handle, "startSystemMove"):
            handle.startSystemMove()

    @Slot(str)
    def window_start_resize(self, edge: str) -> None:
        if not self._window:
            return
        if hasattr(self._window, "_start_resize"):
            self._window._start_resize(edge)

    @Slot(int, int)
    def window_apply_snap(self, screen_x: int, screen_y: int) -> None:
        if not self._window:
            return
        if hasattr(self._window, "_apply_snap"):
            self._window._apply_snap(screen_x, screen_y)

    @Slot(int, int)
    def window_show_system_menu(self, screen_x: int, screen_y: int) -> None:
        if not self._window:
            return
        if hasattr(self._window, "_show_system_menu"):
            self._window._show_system_menu(screen_x, screen_y)

    def _emit_bytes(self, payload: bytes | str | Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(payload, dict):
            return payload
        if isinstance(payload, bytes):
            text = payload.decode(errors="ignore")
            hex_text = payload.hex().upper()
        else:
            text = str(payload)
            hex_text = text.encode().hex().upper()
        return {"text": text, "hex": hex_text, "ts": time.time()}

    def _build_channel_list(self) -> List[Dict[str, Any]]:
        info = dict(self._channel_state)
        if self._comm and hasattr(self._comm, "get_status"):
            status = self._comm.get_status()
            if status:
                info.update(status)
                info["status"] = "connected"
                info["error"] = None
        if not info.get("type"):
            return []
        channel_type = "serial" if info["type"] == "serial" else "tcp-client"
        channel_id = info.get("address") or info.get("port") or channel_type
        return [
            {
                "id": f"{channel_type}:{channel_id}",
                "type": channel_type,
                "status": info.get("status") or "disconnected",
                "port": info.get("port"),
                "baud": info.get("baud"),
                "host": info.get("host"),
                "address": info.get("address"),
                "error": info.get("error") or "",
                "tx_bytes": self._traffic.get("tx", 0),
                "rx_bytes": self._traffic.get("rx", 0),
            }
        ]

    def _emit_channel_update(self, force: bool = False) -> None:
        now = time.time()
        if not force and now - self._last_channel_emit < 0.5:
            return
        self._last_channel_emit = now
        self.channel_update.emit(self._build_channel_list())

    @Slot(str)
    def _emit_comm_rx_signal(self, payload: str) -> None:
        self.comm_rx.emit(payload)

    @Slot(str)
    def _emit_comm_tx_signal(self, payload: str) -> None:
        self.comm_tx.emit(payload)

    @Slot("QVariant")
    def _emit_capture_frame_signal(self, payload: Any) -> None:
        self.capture_frame.emit(payload)

    def _on_comm_rx(self, payload: Any) -> None:
        if isinstance(payload, (bytes, bytearray)):
            self._traffic["rx"] += len(payload)
        payload_dict = self._emit_bytes(payload)
        self._append_buffer(
            {
                "kind": "RX",
                "payload": payload_dict,
                "text": payload_dict.get("text"),
                "hex": payload_dict.get("hex"),
                "ts": payload_dict.get("ts"),
            }
        )
        payload_json = json.dumps(payload_dict, ensure_ascii=False)
        QMetaObject.invokeMethod(
            self,
            "_emit_comm_rx_signal",
            Qt.QueuedConnection,
            Q_ARG(str, payload_json),
        )
        self._emit_channel_update()

    def _on_comm_tx(self, payload: Any) -> None:
        if isinstance(payload, (bytes, bytearray)):
            self._traffic["tx"] += len(payload)
        payload_dict = self._emit_bytes(payload)
        self._append_buffer(
            {
                "kind": "TX",
                "payload": payload_dict,
                "text": payload_dict.get("text"),
                "hex": payload_dict.get("hex"),
                "ts": payload_dict.get("ts"),
            }
        )
        payload_json = json.dumps(payload_dict, ensure_ascii=False)
        QMetaObject.invokeMethod(
            self,
            "_emit_comm_tx_signal",
            Qt.QueuedConnection,
            Q_ARG(str, payload_json),
        )
        self._emit_channel_update()

    def _on_comm_status(self, payload: Any) -> None:
        now = time.time()
        if now < self._last_status_ts:
            return
        self._last_status_ts = now
        self._connect_inflight = False
        if payload is None:
            reason = None
            if self._manual_disconnect:
                reason = "manual"
            elif self._last_error and (now - self._last_error_ts) < 2.0:
                reason = self._last_error
            self._channel_state["status"] = "disconnected"
            self._manual_disconnect = False
        elif isinstance(payload, str):
            self._channel_state["status"] = "error"
            self._channel_state["error"] = payload
            self._last_error = payload
            self._last_error_ts = now
        elif isinstance(payload, dict):
            self._channel_state["type"] = payload.get("type")
            self._channel_state["port"] = payload.get("port")
            self._channel_state["baud"] = payload.get("baud")
            self._channel_state["host"] = payload.get("host")
            self._channel_state["address"] = payload.get("address")
            self._channel_state["status"] = "connected"
            self._channel_state["error"] = None
            self._traffic = {"tx": 0, "rx": 0}
            self._manual_disconnect = False
        event_payload = {"payload": payload, "ts": now}
        if payload is None:
            event_payload["reason"] = reason
        self.comm_status.emit(event_payload)
        self._emit_channel_update(force=True)

    def _on_protocol_frame(self, payload: Any) -> None:
        self._append_buffer({"kind": "FRAME", "payload": payload, "ts": time.time()})

    def _on_capture_frame(self, payload: Any) -> None:
        self._append_buffer({"kind": "CAPTURE", "payload": payload, "ts": time.time()})
        QMetaObject.invokeMethod(
            self,
            "_emit_capture_frame_signal",
            Qt.QueuedConnection,
            Q_ARG(object, payload),
        )

    def _load_protocols(self) -> None:
        if self._protocols_loaded:
            return
        self._protocols_loaded = True
        try:
            for module in pkgutil.iter_modules(protocols_pkg.__path__):
                importlib.import_module(f"{protocols_pkg.__name__}.{module.name}")
        except Exception as exc:  # pragma: no cover - optional UI detail
            self.log.emit(f"[WARN] Load protocols failed: {exc}")

    @staticmethod
    def _protocol_category(key: str) -> str:
        name = (key or "").lower()
        if name.startswith("modbus_"):
            return "modbus"
        if "tcp" in name:
            return "tcp"
        return "custom"

    def _settings_defaults(self) -> Dict[str, Any]:
        base_path = (self._settings_root / "workflows").resolve()
        return {
            "uiLanguage": "Simplified Chinese",
            "uiTheme": "Dark",
            "autoConnectOnStart": True,
            "dslWorkspacePath": str(base_path),
            "serial": {
                "defaultBaud": 115200,
                "defaultParity": "none",
                "defaultStopBits": "1",
            },
            "network": {
                "tcpTimeoutMs": 5000,
                "tcpHeartbeatSec": 60,
                "tcpRetryCount": 3,
            },
        }

    def _load_settings(self) -> Dict[str, Any]:
        defaults = self._settings_defaults()
        if not self._settings_path.exists():
            return defaults
        try:
            with self._settings_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle) or {}
        except Exception:
            return defaults
        if not isinstance(data, dict):
            return defaults
        merged = {
            **defaults,
            **data,
            "serial": {**defaults.get("serial", {}), **(data.get("serial", {}) or {})},
            "network": {**defaults.get("network", {}), **(data.get("network", {}) or {})},
        }
        return merged

    def _save_settings(self, payload: Dict[str, Any]) -> bool:
        if not isinstance(payload, dict):
            return False
        try:
            self._settings_path.parent.mkdir(parents=True, exist_ok=True)
            with self._settings_path.open("w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
        except Exception as exc:
            self.log.emit(f"[WARN] Save settings failed: {exc}")
            return False
        return True

    def _load_proxy_pairs(self) -> List[Dict[str, Any]]:
        if not self._proxy_pairs_path.exists():
            return []
        try:
            with self._proxy_pairs_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle) or []
        except Exception:
            return []
        if not isinstance(data, list):
            return []
        return [item for item in data if isinstance(item, dict)]

    def _save_proxy_pairs(self) -> None:
        try:
            self._proxy_pairs_path.parent.mkdir(parents=True, exist_ok=True)
            with self._proxy_pairs_path.open("w", encoding="utf-8") as handle:
                json.dump(self._proxy_pairs, handle, ensure_ascii=False, indent=2)
        except Exception as exc:
            self.log.emit(f"[WARN] Save proxy pairs failed: {exc}")

    def _load_custom_protocols(self) -> List[Dict[str, Any]]:
        if not self._protocols_path.exists():
            return []
        try:
            with self._protocols_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle) or []
        except Exception:
            return []
        if not isinstance(data, list):
            return []
        items = [item for item in data if isinstance(item, dict)]
        return items

    def _save_custom_protocols(self) -> None:
        try:
            self._protocols_path.parent.mkdir(parents=True, exist_ok=True)
            with self._protocols_path.open("w", encoding="utf-8") as handle:
                json.dump(self._custom_protocols, handle, ensure_ascii=False, indent=2)
        except Exception as exc:
            self.log.emit(f"[WARN] Save protocols failed: {exc}")

    def _normalize_protocol_key(self, value: str) -> str:
        value = value.strip().lower().replace(" ", "_")
        value = re.sub(r"[^a-z0-9_]+", "_", value)
        value = re.sub(r"_+", "_", value).strip("_")
        return value or "custom_protocol"

    def _ensure_protocol_key_unique(self, key: str) -> str:
        registry_keys = set(ProtocolRegistry.list().keys())
        existing = {item.get("id") for item in self._custom_protocols if isinstance(item, dict)}
        existing.update({item.get("key") for item in self._custom_protocols if isinstance(item, dict)})
        existing.update(registry_keys)
        if key not in existing:
            return key
        index = 2
        candidate = f"{key}_{index}"
        while candidate in existing:
            index += 1
            candidate = f"{key}_{index}"
        return candidate

    def _append_buffer(self, item: Dict[str, Any]) -> None:
        self._buffer.append(item)
        if len(self._buffer) > 2000:
            self._buffer = self._buffer[-1000:]

    def _flush_buffers(self) -> None:
        if not self._buffer:
            return
        batch = self._buffer[:]
        self._buffer.clear()
        payload_json = json.dumps(batch, ensure_ascii=False, default=str)
        self.comm_batch.emit(payload_json)
