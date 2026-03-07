from __future__ import annotations

import argparse
import queue
import statistics
import threading
import time
from dataclasses import dataclass, field
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
    samples_ms: List[float] = field(default_factory=list)


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


def _await_exact(port: _Endpoint, expect: bytes, timeout_sec: float) -> bool:
    deadline = time.time() + timeout_sec
    buf = bytearray()
    while time.time() < deadline:
        waiting = port.in_waiting
        if waiting > 0:
            buf.extend(port.read(waiting))
            if bytes(buf) == expect:
                return True
            if len(buf) > len(expect):
                return False
        time.sleep(0.002)
    return False


def _roundtrip(src: _Endpoint, dst: _Endpoint, payload: bytes, timeout_sec: float) -> tuple[bool, float]:
    t0 = time.perf_counter()
    src.write(payload)
    ok = _await_exact(dst, payload, timeout_sec)
    return ok, (time.perf_counter() - t0) * 1000.0


def _wait_status(
    q: "queue.Queue[Dict[str, Any]]",
    pair_id: str,
    status: str,
    timeout_sec: float,
) -> bool:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        try:
            evt = q.get(timeout=0.1)
        except queue.Empty:
            continue
        if evt.get("pair_id") == pair_id and evt.get("status") == status:
            return True
    return False


def _wait_data_event(q: "queue.Queue[Dict[str, Any]]", pair_id: str, timeout_sec: float) -> bool:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        try:
            evt = q.get(timeout=0.1)
        except queue.Empty:
            continue
        if evt.get("pair_id") == pair_id and evt.get("src_role") in {"host", "device"}:
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Mock proxy regression without serial driver.")
    parser.add_argument("--iterations", type=int, default=20)
    parser.add_argument("--payload-size", type=int, default=32)
    parser.add_argument("--timeout-sec", type=float, default=2.0)
    parser.add_argument("--soak-sec", type=int, default=0)
    parser.add_argument("--inject-disconnect", action="store_true")
    args = parser.parse_args()

    pfm.serial.Serial = _fake_serial_ctor  # type: ignore[assignment]
    EventBus._log = staticmethod(lambda _message: None)  # type: ignore[method-assign]
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
            print(f"[{'PASS' if r.passed else 'FAIL'}] {r.name} {r.detail}".rstrip())
        print("RESULT: FAILED")
        return 2

    t_host = _fake_serial_ctor("VCOM12")
    t_device = _fake_serial_ctor("VCOM14")

    h2d_samples: List[float] = []
    d2h_samples: List[float] = []
    loops_ok = True
    loops_msg = "ok"
    for _ in range(max(1, args.iterations)):
        payload_1 = bytes([0x01, 0x03]) + bytes([0xA5] * max(1, args.payload_size))
        ok_1, lat_1 = _roundtrip(t_host, t_device, payload_1, args.timeout_sec)
        if not ok_1:
            loops_ok = False
            loops_msg = "host_to_device payload mismatch/timeout"
            break
        h2d_samples.append(lat_1)

        payload_2 = bytes([0x01, 0x04]) + bytes([0x5A] * max(1, args.payload_size))
        ok_2, lat_2 = _roundtrip(t_device, t_host, payload_2, args.timeout_sec)
        if not ok_2:
            loops_ok = False
            loops_msg = "device_to_host payload mismatch/timeout"
            break
        d2h_samples.append(lat_2)
    results.append(TestResult("bidirectional_loop", loops_ok, loops_msg, h2d_samples + d2h_samples))

    evt_ok = _wait_data_event(data_events, pair_id, args.timeout_sec)
    results.append(TestResult("proxy.data_event", evt_ok, "" if evt_ok else "no proxy.data event"))

    if args.soak_sec > 0 and loops_ok:
        soak_ok = True
        soak_msg = "ok"
        soak_samples: List[float] = []
        end = time.time() + args.soak_sec
        flip = True
        while time.time() < end:
            payload = b"\xAA\x55" + bytes([0x11] * 16)
            if flip:
                ok, lat = _roundtrip(t_host, t_device, payload, args.timeout_sec)
            else:
                ok, lat = _roundtrip(t_device, t_host, payload, args.timeout_sec)
            if not ok:
                soak_ok = False
                soak_msg = "soak timeout/mismatch"
                break
            soak_samples.append(lat)
            flip = not flip
            time.sleep(0.01)
        results.append(TestResult("soak.forwarding", soak_ok, soak_msg, soak_samples))

    if args.inject_disconnect:
        # Simulate device unplug: test endpoint closes, then next write should trigger proxy error.
        t_device.close()
        disconnect_observed = False
        disconnect_msg = "no error event"
        try:
            t_host.write(b"\x10\x20\x30")
        except Exception:
            pass
        deadline = time.time() + args.timeout_sec
        while time.time() < deadline:
            try:
                evt = status_events.get(timeout=0.1)
            except queue.Empty:
                continue
            if evt.get("pair_id") == pair_id and evt.get("status") == "error":
                disconnect_observed = True
                disconnect_msg = str(evt.get("error") or "")
                break
        results.append(
            TestResult(
                "fault.disconnect_error_event",
                disconnect_observed,
                disconnect_msg if not disconnect_observed else "error event observed",
            )
        )

    manager.stop_pair(pair_id)
    stopped_ok = _wait_status(status_events, pair_id, "stopped", args.timeout_sec)
    results.append(TestResult("status.stopped", stopped_ok, "" if stopped_ok else "no stopped event"))

    passed = all(r.passed for r in results)
    for r in results:
        line = f"[{'PASS' if r.passed else 'FAIL'}] {r.name}"
        if r.samples_ms:
            avg = statistics.mean(r.samples_ms)
            line += f" avg={avg:.3f}ms n={len(r.samples_ms)}"
        if r.detail:
            line += f" | {r.detail}"
        print(line)
    print(f"RESULT: {'PASSED' if passed else 'FAILED'}")
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
