from __future__ import annotations

import queue
import socket
import threading
import time
from dataclasses import dataclass
from typing import Optional, Tuple

try:
    import serial
except Exception:  # pragma: no cover
    serial = None


class Endpoint:
    def read(self, size: int, timeout: float) -> bytes:
        raise NotImplementedError

    def write(self, data: bytes) -> None:
        raise NotImplementedError

    def close(self) -> None:
        return None


class SerialEndpoint(Endpoint):
    def __init__(self, port: str, baud: int) -> None:
        if serial is None:
            raise RuntimeError("pyserial is required for serial mode")
        self._ser = serial.Serial(port=port, baudrate=baud, timeout=0, write_timeout=0.5)

    def read(self, size: int, timeout: float) -> bytes:
        deadline = time.time() + max(0.01, timeout)
        buf = bytearray()
        while len(buf) < size and time.time() < deadline:
            chunk = self._ser.read(size - len(buf))
            if chunk:
                buf.extend(chunk)
            else:
                time.sleep(0.005)
        return bytes(buf)

    def write(self, data: bytes) -> None:
        self._ser.write(data)

    def close(self) -> None:
        try:
            self._ser.close()
        except Exception:
            pass


class TcpServerEndpoint(Endpoint):
    def __init__(self, host: str, port: int) -> None:
        self._srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._srv.bind((host, port))
        self._srv.listen(1)
        self._srv.settimeout(15.0)
        self._conn, _ = self._srv.accept()
        self._conn.settimeout(0.1)

    def read(self, size: int, timeout: float) -> bytes:
        deadline = time.time() + max(0.01, timeout)
        while time.time() < deadline:
            try:
                data = self._conn.recv(max(1, size))
                return data
            except socket.timeout:
                continue
        return b""

    def write(self, data: bytes) -> None:
        self._conn.sendall(data)

    def close(self) -> None:
        for s in [self._conn, self._srv]:
            try:
                s.close()
            except Exception:
                pass


@dataclass
class MockDuplexEndpoint(Endpoint):
    rx: "queue.Queue[bytes]"
    tx: "queue.Queue[bytes]"
    _closed: bool = False

    def read(self, size: int, timeout: float) -> bytes:
        if self._closed:
            return b""
        deadline = time.time() + max(0.01, timeout)
        out = bytearray()
        while len(out) < size and time.time() < deadline:
            try:
                chunk = self.rx.get(timeout=min(0.02, max(0.001, deadline - time.time())))
            except queue.Empty:
                continue
            if not chunk:
                continue
            out.extend(chunk[: max(1, size - len(out))])
        return bytes(out)

    def write(self, data: bytes) -> None:
        if self._closed:
            return
        self.tx.put(bytes(data))

    def close(self) -> None:
        self._closed = True


def create_mock_pair() -> Tuple[MockDuplexEndpoint, MockDuplexEndpoint]:
    a2b: "queue.Queue[bytes]" = queue.Queue()
    b2a: "queue.Queue[bytes]" = queue.Queue()
    return MockDuplexEndpoint(rx=b2a, tx=a2b), MockDuplexEndpoint(rx=a2b, tx=b2a)


class TcpClient:
    def __init__(self, host: str, port: int) -> None:
        self._sock = socket.create_connection((host, port), timeout=3.0)
        self._sock.settimeout(0.1)

    def write(self, data: bytes) -> None:
        self._sock.sendall(data)

    def read(self, size: int = 512, timeout: float = 0.5) -> bytes:
        deadline = time.time() + max(0.01, timeout)
        while time.time() < deadline:
            try:
                return self._sock.recv(size)
            except socket.timeout:
                continue
        return b""

    def close(self) -> None:
        try:
            self._sock.close()
        except Exception:
            pass
