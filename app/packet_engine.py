"""Packet analysis engine for streaming capture frames.

Subscribes to comm.rx/comm.tx and publishes structured frame data to the bus.
"""

from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

from infra.common.event_bus import EventBus
from infra.protocol.protocol_loader import crc16_modbus


@dataclass
class _ChannelInfo:
    channel: str = ""
    port: Optional[str] = None
    baud: Optional[int] = None
    host: Optional[str] = None
    address: Optional[str] = None


class PacketAnalysisEngine:
    """Streaming packet parser that emits capture.frame events."""

    def __init__(self, bus: EventBus) -> None:
        self._bus = bus
        self._queue: "queue.Queue[Tuple[str, bytes, float]]" = queue.Queue()
        self._channel = _ChannelInfo()
        self._enabled = False
        self._target_channel: Optional[str] = None
        self._counter = 0
        self._stop = threading.Event()
        self._worker = threading.Thread(target=self._run, daemon=True)
        self._worker.start()
        self._bus.subscribe("comm.rx", self._on_rx)
        self._bus.subscribe("comm.tx", self._on_tx)
        self._bus.subscribe("comm.connected", self._on_connected)
        self._bus.subscribe("comm.disconnected", self._on_disconnected)
        self._bus.subscribe("capture.control", self._on_control)

    def _on_rx(self, payload: Any) -> None:
        if not self._enabled:
            return
        data = self._to_bytes(payload)
        if data:
            if self._target_channel and self._channel.channel and self._channel.channel != self._target_channel:
                return
            self._queue.put(("RX", data, time.time()))

    def _on_tx(self, payload: Any) -> None:
        if not self._enabled:
            return
        data = self._to_bytes(payload)
        if data:
            if self._target_channel and self._channel.channel and self._channel.channel != self._target_channel:
                return
            self._queue.put(("TX", data, time.time()))

    def _on_connected(self, payload: Any) -> None:
        if isinstance(payload, dict):
            self._channel.port = payload.get("port")
            self._channel.baud = payload.get("baud")
            self._channel.host = payload.get("host")
            self._channel.address = payload.get("address")
            if payload.get("type") == "serial" and self._channel.port:
                self._channel.channel = str(self._channel.port)
            elif payload.get("type") == "tcp-client":
                self._channel.channel = f"{self._channel.host}:{self._channel.address}" if self._channel.host else ""

    def _on_disconnected(self, payload: Any) -> None:
        self._channel = _ChannelInfo()

    def _on_control(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        action = payload.get("action")
        if action == "start":
            self._enabled = True
            channel = payload.get("channel")
            self._target_channel = str(channel) if channel else None
        elif action == "stop":
            self._enabled = False
            self._target_channel = None

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                direction, data, ts = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue
            frame = self._build_frame(direction, data, ts)
            self._bus.publish("capture.frame", frame)
            self._queue.task_done()

    def _build_frame(self, direction: str, data: bytes, ts: float) -> Dict[str, Any]:
        self._counter += 1
        hex_bytes = [f"{b:02X}" for b in data]
        ascii_str = "".join(chr(b) if 32 <= b <= 126 else "." for b in data)
        ascii_lines = self._split_ascii(ascii_str, 8)
        protocol_name, protocol_unknown, summary, tree_rows, errors = self._parse_protocol(data)
        channel = self._channel.channel or ""
        frame_id = f"{direction.lower()}-{int(ts * 1000)}-{self._counter}"
        return {
            "id": frame_id,
            "timestamp": ts,
            "direction": direction,
            "channel": channel,
            "baud": self._channel.baud,
            "length": len(data),
            "raw_hex": " ".join(hex_bytes),
            "ascii": ascii_str,
            "protocol": {
                "name": protocol_name,
                "unknown": protocol_unknown,
                "confidence": 0.9 if not protocol_unknown else 0.2,
            },
            "summary": summary,
            "hex_dump": {
                "bytes": hex_bytes,
                "ascii_lines": ascii_lines,
                "size": len(data),
            },
            "tree": tree_rows,
            "errors": errors,
        }

    def _parse_protocol(
        self, data: bytes
    ) -> Tuple[str, bool, str, List[Dict[str, str]], List[Dict[str, str]]]:
        if len(data) < 2:
            return "Unknown", True, "Too short", [], []

        addr = data[0]
        func = data[1]
        summary = f"addr=0x{addr:02X} func=0x{func:02X} len={len(data)}"
        tree = [
            {"label": "Address", "raw": f"{addr:02X}", "value": str(addr)},
            {"label": "Function", "raw": f"{func:02X}", "value": f"0x{func:02X}"},
        ]

        if len(data) >= 4:
            crc_ok = self._check_modbus_crc(data)
            tree.append(
                {
                    "label": "CRC16",
                    "raw": " ".join(f"{b:02X}" for b in data[-2:]),
                    "value": "valid" if crc_ok else "invalid",
                }
            )
            if crc_ok:
                return "Modbus RTU", False, summary, tree, []

        errors = [{"code": "UNKNOWN_PROTOCOL", "message": "No known signature"}]
        return "Unknown", True, summary, tree, errors

    @staticmethod
    def _check_modbus_crc(data: bytes) -> bool:
        if len(data) < 3:
            return False
        body = data[:-2]
        expected = int.from_bytes(data[-2:], "little")
        return crc16_modbus(body) == expected

    @staticmethod
    def _split_ascii(text: str, width: int) -> List[str]:
        return [text[i : i + width] for i in range(0, len(text), width)] or [""]

    @staticmethod
    def _to_bytes(payload: Any) -> bytes:
        if isinstance(payload, (bytes, bytearray)):
            return bytes(payload)
        if isinstance(payload, str):
            return payload.encode(errors="ignore")
        return b""
