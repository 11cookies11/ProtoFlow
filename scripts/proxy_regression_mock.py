from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from infra.common.event_bus import EventBus
import infra.comm.proxy_forward_manager as pfm


@dataclass
class TestResult:
    name: str
    passed: bool
    detail: str = ""


class _Endpoint:
    def __init__(self, name: str) -> None:
        self.name = name
        self.peer: Optional["_Endpoint"] = None
        self.rx = queue.Queue()
        self.is_open = True

    @property
    def in_waiting(self) -> int:
        return self.rx.qsize()

    def read(self, size: int) -> bytes:
        data = bytearray()
        for _ in range(max(0, size)):
            try:
                data.extend(self.rx.get_nowait())
            except queue.Empty:
                break
        return bytes(data)

    def write(self, data: bytes) -> int:
        if not self.is_open:
            raise OSError("port closed")
        if not self.peer or not self.peer.is_open:
            raise OSError("peer closed")
        for b in data:
            self.peer.rx.put(bytes([b]))
        return len(data)

    def close(self) -> None:
        self.is_open = False


_endpoints: Dict[str, _Endpoint] = {}
_pairs = {
    "VCOM11": "VCOM12",
    "VCOM12": "VCOM11",
    "VCOM13": "VCOM14",
    "VCOM14": "VCOM13",
}
_lock = threading.Lock()


def _fake_serial_ctor(port: str, **_: Any) -> _Endpoint:
    with _lock:
        if port not in _pairs:
            raise OSError(f"unknown virtual port: {port}")
        ep = _endpoints.get(port)
        if ep is None or not ep.is_open:
            ep = _Endpoint(port)
            _endpoints[port] = ep
        peer_name = _pairs[port]
        peer = _endpoints.get(peer_name)
        if peer is None or not peer.is_open:
            peer = _Endpoint(peer_name)
            _endpoints[peer_name] = peer
        ep.peer = peer
        peer.peer = ep
        return ep


def _await_bytes(port: _Endpoint, expect: bytes, timeout: float = 2.0) -> bool:
    deadline = time.time() + timeout
    buf = bytearray()
    while time.time() < deadline:
        waiting = port.in_waiting
        if waiting > 0:
            buf.extend(port.read(waiting))
            if bytes(buf) == expect:
                return True
            if len(buf) > len(expect):
                return False
        time.sleep(0.005)
    return False


def main() -> int:
    pfm.serial.Serial = _fake_serial_ctor  # type: ignore[assignment]

    bus = EventBus()
    manager = pfm.ProxyForwardManager(bus)
    status_events: "queue.Queue[Dict[str, Any]]" = queue.Queue()
    data_events: "queue.Queue[Dict[str, Any]]" = queue.Queue()
    bus.subscribe("proxy.status", lambda p: status_events.put(p if isinstance(p, dict) else {}))
    bus.subscribe("proxy.data", lambda p: data_events.put(p if isinstance(p, dict) else {}))

    pair_id = "mock-pair-1"
    cfg = {
        "hostPort": "VCOM11",
        "devicePort": "VCOM13",
        "baud": "115200",
        "dataBits": "8",
        "stopBits": "1",
        "parity": "none",
        "flowControl": "none",
    }

    results: List[TestResult] = []

    start = manager.start_pair(pair_id, cfg)
    results.append(TestResult("start_pair", start.ok, start.error))
    if not start.ok:
        for r in results:
            print(f"[{'PASS' if r.passed else 'FAIL'}] {r.name} {r.detail}")
        return 2

    t_host = _fake_serial_ctor("VCOM12")
    t_device = _fake_serial_ctor("VCOM14")

    payload_1 = b"\x01\x03\x00\x00\x00\x02\xC4\x0B"
    t0 = time.time()
    t_host.write(payload_1)
    ok_h2d = _await_bytes(t_device, payload_1)
    latency_h2d = (time.time() - t0) * 1000.0
    results.append(
        TestResult("host_to_device", ok_h2d, "" if ok_h2d else "payload mismatch or timeout")
    )

    payload_2 = b"\x01\x03\x04\x00\x01\x00\x02\x2A\x32"
    t1 = time.time()
    t_device.write(payload_2)
    ok_d2h = _await_bytes(t_host, payload_2)
    latency_d2h = (time.time() - t1) * 1000.0
    results.append(
        TestResult("device_to_host", ok_d2h, "" if ok_d2h else "payload mismatch or timeout")
    )

    evt_ok = False
    evt_deadline = time.time() + 2.0
    while time.time() < evt_deadline:
        try:
            evt = data_events.get(timeout=0.1)
        except queue.Empty:
            continue
        if evt.get("pair_id") == pair_id and evt.get("src_role") in {"host", "device"}:
            evt_ok = True
            break
    results.append(TestResult("proxy.data_event", evt_ok, "" if evt_ok else "no proxy.data event"))

    manager.stop_pair(pair_id)
    stopped_ok = False
    end = time.time() + 2.0
    while time.time() < end:
        try:
            evt = status_events.get(timeout=0.1)
        except queue.Empty:
            continue
        if evt.get("pair_id") == pair_id and evt.get("status") == "stopped":
            stopped_ok = True
            break
    results.append(TestResult("status.stopped", stopped_ok, "" if stopped_ok else "no stopped event"))

    passed = all(r.passed for r in results)
    for r in results:
        print(f"[{'PASS' if r.passed else 'FAIL'}] {r.name} {r.detail}".rstrip())
    print(f"[INFO] latency host->device: {latency_h2d:.3f} ms")
    print(f"[INFO] latency device->host: {latency_d2h:.3f} ms")
    print(f"RESULT: {'PASSED' if passed else 'FAILED'}")
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
