"""固件升级插件：通过 ProtocolLoader 发送 ERASE / WRITE / FINISH 流程。"""

from __future__ import annotations

import time
from pathlib import Path

PLUGIN_NAME = "ota_upgrade"


def register(bus, protocol):
    ctx = _OtaContext(bus, protocol)
    bus.subscribe("protocol.frame", ctx.on_frame)
    bus.subscribe("ui.start_upgrade", ctx.on_start)


class _OtaContext:
    def __init__(self, bus, protocol) -> None:
        self.bus = bus
        self.protocol = protocol
        self.current_state = "idle"
        self.firmware_data: bytes = b""
        self.write_offset = 0
        self.block_size = self._load_block_size()

    def _load_block_size(self) -> int:
        try:
            cfg = getattr(self.protocol, "config", {}) or {}
            ota_cfg = cfg.get("ota", {})
            return int(ota_cfg.get("block_size", 256))
        except Exception:
            return 256

    def on_start(self, payload) -> None:
        """接收 UI 触发，payload 为固件文件路径。"""
        path = Path(payload) if isinstance(payload, (str, Path)) else None
        if not path or not path.exists():
            self.bus.publish("ota.error", f"固件不存在: {payload}")
            return

        try:
            self.firmware_data = path.read_bytes()
        except Exception as exc:
            self.bus.publish("ota.error", f"读取固件失败: {exc}")
            return

        self.write_offset = 0
        self.current_state = "erase"
        self.bus.publish("ota.status", "ERASE START")
        self._send_cmd("erase")

    def on_frame(self, frame) -> None:
        cmd = frame.get("cmd") if isinstance(frame, dict) else None
        if not cmd:
            return

        if self.current_state == "erase" and cmd == "erase":
            self.bus.publish("ota.status", "ERASE DONE")
            self.current_state = "write"
            self._write_next_block()
            return

        if self.current_state == "write" and cmd == "write":
            self._write_next_block()
            return

        if self.current_state == "finish" and cmd == "finish":
            self.current_state = "done"
            self.bus.publish("ota.finished", "SUCCESS")
            return

    def _write_next_block(self) -> None:
        if self.write_offset >= len(self.firmware_data):
            self.current_state = "finish"
            self.bus.publish("ota.status", "FINISH SEND")
            self._send_cmd("finish")
            return

        end = min(self.write_offset + self.block_size, len(self.firmware_data))
        chunk = self.firmware_data[self.write_offset : end]
        self._send_cmd("write", chunk)
        self.write_offset = end
        progress = f"WRITE {self.write_offset}/{len(self.firmware_data)}"
        self.bus.publish("ota.status", progress)

    def _send_cmd(self, cmd_name: str, payload: bytes = b"") -> None:
        try:
            frame = self.protocol.send(cmd_name, payload)
            # ProtocolLoader.publish("protocol.tx", frame) 已包含在 send 内
            self.bus.publish("ota.debug", f"TX {cmd_name} len={len(payload)}")
        except Exception as exc:
            self.bus.publish("ota.error", f"发送 {cmd_name} 失败: {exc}")
