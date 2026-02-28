from __future__ import annotations

import queue
import time
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from infra.common.event_bus import EventBus
import infra.comm.communication_manager as cm


class _FakeSerialManager:
    def __init__(self, bus: EventBus) -> None:
        self._bus = bus
        self._open = False
        self.port = None
        self.baudrate = None

    def open(self, port: str, baudrate: int) -> bool:
        self.port = port
        self.baudrate = baudrate
        self._open = True
        self._bus.publish("serial.opened", port)
        return True

    def close(self) -> None:
        self._open = False
        self._bus.publish("serial.closed")

    def is_open(self) -> bool:
        return self._open

    def send(self, _data: bytes) -> None:
        pass

    @staticmethod
    def list_ports() -> list[str]:
        return ["COM1", "COM2"]


class _FakeTcpSession:
    def __init__(self, bus: EventBus) -> None:
        self._bus = bus
        self._connected = False
        self.endpoint = None

    def connect(self, ip: str, port: int) -> None:
        self.endpoint = (ip, port)
        self._connected = True

    def is_connected(self) -> bool:
        return self._connected

    def close(self) -> None:
        self._connected = False
        self._bus.publish("tcp.disconnected")

    def send(self, _data: bytes) -> None:
        pass


def _wait_event(q: "queue.Queue[dict]", kind: str, timeout: float = 2.0) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        try:
            evt = q.get(timeout=0.1)
        except queue.Empty:
            continue
        if evt.get("kind") == kind:
            return True
    return False


def main() -> int:
    cm.SerialManager = _FakeSerialManager  # type: ignore[assignment]
    cm.TcpSession = _FakeTcpSession  # type: ignore[assignment]
    EventBus._log = staticmethod(lambda _message: None)  # type: ignore[method-assign]

    bus = EventBus()
    events: "queue.Queue[dict]" = queue.Queue()
    bus.subscribe("comm.connected", lambda p: events.put({"kind": "connected", "payload": p}))
    bus.subscribe("comm.disconnected", lambda p: events.put({"kind": "disconnected", "payload": p}))
    bus.subscribe("comm.error", lambda p: events.put({"kind": "error", "payload": p}))

    mgr = cm.CommunicationManager(bus)

    mgr.select_serial("COM1", 115200)
    serial_connected = _wait_event(events, "connected")

    mgr.close(notify=True)
    serial_disconnected = _wait_event(events, "disconnected")

    mgr.select_tcp("127.0.0.1", 9000)
    tcp_connected = _wait_event(events, "connected")

    mgr.close(notify=True)
    tcp_disconnected = _wait_event(events, "disconnected")

    checks = [
        ("serial_connected", serial_connected),
        ("serial_disconnected", serial_disconnected),
        ("tcp_connected", tcp_connected),
        ("tcp_disconnected", tcp_disconnected),
    ]
    ok = True
    for name, passed in checks:
        print(f"[{'PASS' if passed else 'FAIL'}] {name}")
        ok = ok and passed
    print(f"RESULT: {'PASSED' if ok else 'FAILED'}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
