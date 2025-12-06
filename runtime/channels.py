from __future__ import annotations

import socket
import time
from typing import Any, Dict

try:
    import serial
except ImportError:  # pragma: no cover
    serial = None


class BaseChannel:
    def write(self, data: bytes | str):
        raise NotImplementedError()

    def read(self, size: int = 1, timeout: float = 1.0) -> bytes:
        raise NotImplementedError()

    def read_exact(self, size: int, timeout: float = 1.0) -> bytes:
        buf = bytearray()
        deadline = time.time() + timeout
        while len(buf) < size and time.time() < deadline:
            chunk = self.read(size - len(buf), timeout=max(0.01, deadline - time.time()))
            if chunk:
                buf.extend(chunk)
            else:
                time.sleep(0.01)
        return bytes(buf)

    def read_until(self, terminator: bytes, timeout: float = 1.0) -> bytes:
        buf = bytearray()
        deadline = time.time() + timeout
        while time.time() < deadline:
            chunk = self.read(1, timeout=max(0.01, deadline - time.time()))
            if chunk:
                buf.extend(chunk)
                if buf.endswith(terminator):
                    break
            else:
                time.sleep(0.01)
        return bytes(buf)

    def read_event(self, timeout: float = 0.1):
        data = self.read(1, timeout=timeout)
        if not data:
            return None
        try:
            return data.decode(errors="ignore")
        except Exception:
            return data.hex().upper()


class SerialChannel(BaseChannel):
    def __init__(self, cfg: Dict[str, Any]) -> None:
        if serial is None:
            raise ImportError("未安装 pyserial，无法使用串口通道")
        self.ser = serial.Serial(
            port=cfg["device"],
            baudrate=int(cfg.get("baudrate", 115200)),
            timeout=0,
        )

    def write(self, data: bytes | str):
        payload = data.encode() if isinstance(data, str) else data
        self.ser.write(payload)

    def read(self, size: int = 1, timeout: float = 1.0) -> bytes:
        deadline = time.time() + timeout
        buf = bytearray()
        while len(buf) < size and time.time() < deadline:
            chunk = self.ser.read(size - len(buf))
            if chunk:
                buf.extend(chunk)
            else:
                time.sleep(0.01)
        return bytes(buf)


class TcpChannel(BaseChannel):
    def __init__(self, cfg: Dict[str, Any]) -> None:
        self.sock = socket.create_connection((cfg["host"], int(cfg["port"])), timeout=float(cfg.get("timeout", 2.0)))
        self.sock.settimeout(0.2)

    def write(self, data: bytes | str):
        payload = data.encode() if isinstance(data, str) else data
        self.sock.sendall(payload)

    def read(self, size: int = 1, timeout: float = 1.0) -> bytes:
        deadline = time.time() + timeout
        buf = bytearray()
        while len(buf) < size and time.time() < deadline:
            try:
                chunk = self.sock.recv(size - len(buf))
                if chunk:
                    buf.extend(chunk)
                else:
                    time.sleep(0.01)
            except socket.timeout:
                continue
        return bytes(buf)


def build_channels(cfg: Dict[str, Any]) -> Dict[str, BaseChannel]:
    channels: Dict[str, BaseChannel] = {}
    for name, ch_cfg in cfg.items():
        typ = ch_cfg.get("type", "uart")
        if typ in {"uart", "serial"}:
            channels[name] = SerialChannel(ch_cfg)
        elif typ == "tcp":
            channels[name] = TcpChannel(ch_cfg)
        else:
            raise ValueError(f"未知通道类型: {typ}")
    return channels
