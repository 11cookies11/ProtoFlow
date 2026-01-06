"""TCP 会话：与 SerialManager 接口风格一致，基于 socket 实现。"""

from __future__ import annotations

import socket
import threading
import time
from typing import Optional

from core.event_bus import EventBus


class TcpSession:
    def __init__(self, bus: EventBus) -> None:
        self.bus = bus
        self._sock: Optional[socket.socket] = None
        self._rx_thread: Optional[threading.Thread] = None
        self._running = False
        self._lock = threading.RLock()
        self._endpoint: Optional[tuple[str, int]] = None

    @property
    def endpoint(self) -> Optional[tuple[str, int]]:
        with self._lock:
            return self._endpoint

    def is_connected(self) -> bool:
        with self._lock:
            return bool(self._sock) and self._running

    def connect(self, ip: str, port: int) -> None:
        """建立 TCP 连接并启动接收线程。"""
        with self._lock:
            self._endpoint = (ip, port)
            self.close()
            try:
                sock = socket.create_connection((ip, port), timeout=3)
                sock.settimeout(0.1)  # 非阻塞轮询
                self._sock = sock
                self._running = True
                self._rx_thread = threading.Thread(target=self._rx_loop, daemon=True)
                self._rx_thread.start()
                self._log(f"TCP 已连接 {ip}:{port}")
                self.bus.publish("tcp.connected", f"{ip}:{port}")
            except OSError as exc:
                self._log(f"[ERROR] 连接失败: {exc}")
                self.bus.publish("tcp.error", str(exc))

    def close(self) -> None:
        """关闭连接并停止接收线程。"""
        with self._lock:
            self._running = False
            if self._rx_thread and self._rx_thread.is_alive():
                self._rx_thread.join(timeout=1)
            if self._sock:
                try:
                    self._sock.close()
                except Exception:
                    pass
                self._sock = None
        self.bus.publish("tcp.disconnected")

    def send(self, data: bytes) -> None:
        """发送数据。"""
        with self._lock:
            sock = self._sock
        if not sock:
            self._log("[WARN] TCP 未连接，发送忽略")
            return
        try:
            sock.sendall(data)
            self.bus.publish("tcp.tx", data)
        except OSError as exc:
            self._log(f"[ERROR] 发送失败: {exc}")
            self.bus.publish("tcp.error", str(exc))

    def _rx_loop(self) -> None:
        """接收线程：非阻塞读取，异常时退出。"""
        while self._running:
            sock = self._sock
            if not sock:
                time.sleep(0.05)
                continue
            try:
                chunk = sock.recv(4096)
                if not chunk:
                    self._log("对端关闭连接")
                    self.bus.publish("tcp.disconnected")
                    self.close()
                    return
                self.bus.publish("tcp.rx", chunk)
            except socket.timeout:
                continue  # 正常轮询
            except OSError as exc:
                self._log(f"[ERROR] 接收异常: {exc}")
                self.bus.publish("tcp.error", str(exc))
                self.close()
                return

    @staticmethod
    def _log(msg: str) -> None:
        print(f"[TcpSession] {msg}")
