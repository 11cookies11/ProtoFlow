from __future__ import annotations

import argparse
import json
import sys
import time
import types
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

HAS_PYSERIAL = True
try:
    from serial import SerialException
except Exception:
    HAS_PYSERIAL = False

    class SerialException(Exception):
        pass

    # Minimal stub so infra.comm.serial_manager can be imported in mock mode.
    serial_stub = types.ModuleType("serial")
    serial_stub.SerialException = SerialException
    serial_stub.Serial = object
    serial_stub.FIVEBITS = 5
    serial_stub.SIXBITS = 6
    serial_stub.SEVENBITS = 7
    serial_stub.EIGHTBITS = 8
    serial_stub.PARITY_NONE = "N"
    serial_stub.PARITY_ODD = "O"
    serial_stub.PARITY_EVEN = "E"
    serial_stub.PARITY_MARK = "M"
    serial_stub.PARITY_SPACE = "S"
    serial_stub.STOPBITS_ONE = 1
    serial_stub.STOPBITS_ONE_POINT_FIVE = 1.5
    serial_stub.STOPBITS_TWO = 2

    serial_tools_stub = types.ModuleType("serial.tools")
    list_ports_stub = types.ModuleType("serial.tools.list_ports")
    list_ports_stub.comports = lambda: []
    serial_tools_stub.list_ports = list_ports_stub
    serial_stub.tools = serial_tools_stub

    sys.modules["serial"] = serial_stub
    sys.modules["serial.tools"] = serial_tools_stub
    sys.modules["serial.tools.list_ports"] = list_ports_stub

from infra.comm.communication_manager import CommunicationManager
from infra.comm.serial_manager import SerialManager
from infra.common.event_bus import EventBus
import infra.comm.serial_manager as serial_module


@dataclass
class GateStats:
    cycles: int = 0
    connect_ok: int = 0
    connect_fail: int = 0
    reconnect_checks: int = 0
    reconnect_ok: int = 0
    reconnect_fail: int = 0
    comm_connecting_events: int = 0
    comm_connected_events: int = 0
    comm_disconnected_events: int = 0
    comm_error_events: int = 0

    def to_dict(self) -> Dict[str, Any]:
        connect_rate = 0.0
        if self.cycles:
            connect_rate = (self.connect_ok / self.cycles) * 100.0
        reconnect_rate = 0.0
        if self.reconnect_checks:
            reconnect_rate = (self.reconnect_ok / self.reconnect_checks) * 100.0
        return {
            "cycles": self.cycles,
            "connect_ok": self.connect_ok,
            "connect_fail": self.connect_fail,
            "connect_success_rate": round(connect_rate, 2),
            "reconnect_checks": self.reconnect_checks,
            "reconnect_ok": self.reconnect_ok,
            "reconnect_fail": self.reconnect_fail,
            "reconnect_success_rate": round(reconnect_rate, 2),
            "events": {
                "comm.connecting": self.comm_connecting_events,
                "comm.connected": self.comm_connected_events,
                "comm.disconnected": self.comm_disconnected_events,
                "comm.error": self.comm_error_events,
            },
        }


class MockSerial:
    fail_open_every: int = 0
    open_count: int = 0

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        type(self).open_count += 1
        if self.fail_open_every > 0 and self.open_count % self.fail_open_every == 0:
            raise SerialException("mock open failure")
        self._buf = bytearray()
        self.is_open = True

    @property
    def in_waiting(self) -> int:
        if not self.is_open:
            raise SerialException("port closed")
        return len(self._buf)

    def read(self, size: int) -> bytes:
        if not self.is_open:
            raise SerialException("port closed")
        if size <= 0 or not self._buf:
            return b""
        size = min(size, len(self._buf))
        out = bytes(self._buf[:size])
        del self._buf[:size]
        return out

    def write(self, data: bytes) -> int:
        if not self.is_open:
            raise SerialException("port closed")
        self._buf.extend(data)
        return len(data)

    def close(self) -> None:
        self.is_open = False


@contextmanager
def patch_serial_for_mock(fail_open_every: int):
    original_ctor = serial_module.serial.Serial
    MockSerial.fail_open_every = max(0, int(fail_open_every))
    MockSerial.open_count = 0
    serial_module.serial.Serial = MockSerial  # type: ignore[assignment]
    try:
        yield
    finally:
        serial_module.serial.Serial = original_ctor  # type: ignore[assignment]


def wait_until_connected(manager: CommunicationManager, timeout_s: float) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        status = manager.get_status()
        if status and status.get("type") == "serial":
            return True
        time.sleep(0.02)
    return False


def run_gate(
    *,
    mode: str,
    port: str,
    baud: int,
    cycles: int,
    threshold: float,
    connect_timeout_s: float,
    settle_ms: int,
    inject_drop_every: int,
    fail_open_every: int,
) -> tuple[GateStats, bool]:
    bus = EventBus()
    manager = CommunicationManager(bus)
    stats = GateStats(cycles=cycles)

    bus.subscribe("comm.connecting", lambda _: setattr(stats, "comm_connecting_events", stats.comm_connecting_events + 1))
    bus.subscribe("comm.connected", lambda _: setattr(stats, "comm_connected_events", stats.comm_connected_events + 1))
    bus.subscribe("comm.disconnected", lambda _: setattr(stats, "comm_disconnected_events", stats.comm_disconnected_events + 1))
    bus.subscribe("comm.error", lambda _: setattr(stats, "comm_error_events", stats.comm_error_events + 1))

    for i in range(1, cycles + 1):
        manager.select_serial(port, baud)
        if wait_until_connected(manager, connect_timeout_s):
            stats.connect_ok += 1
        else:
            stats.connect_fail += 1

        if inject_drop_every > 0 and i % inject_drop_every == 0:
            stats.reconnect_checks += 1
            session = manager._current_session  # intentional for gate diagnostics
            if isinstance(session, SerialManager) and session._ser is not None:
                session._ser.is_open = False  # type: ignore[attr-defined]
                if wait_until_connected(manager, connect_timeout_s + 2.0):
                    stats.reconnect_ok += 1
                else:
                    stats.reconnect_fail += 1
            else:
                stats.reconnect_fail += 1

        manager.close()
        time.sleep(max(0.0, settle_ms / 1000.0))

    manager.close()
    report = stats.to_dict()
    connect_ok = report["connect_success_rate"] >= threshold
    reconnect_ok = (
        report["reconnect_success_rate"] >= threshold
        if stats.reconnect_checks > 0
        else True
    )
    return stats, bool(connect_ok and reconnect_ok)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serial reliability gate for W4-01")
    parser.add_argument("--mode", choices=["mock", "real"], default="mock")
    parser.add_argument("--port", default="COM5")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--cycles", type=int, default=200)
    parser.add_argument("--threshold", type=float, default=99.0)
    parser.add_argument("--connect-timeout-ms", type=int, default=1200)
    parser.add_argument("--settle-ms", type=int, default=30)
    parser.add_argument("--inject-drop-every", type=int, default=20)
    parser.add_argument("--fail-open-every", type=int, default=0)
    parser.add_argument("--json-out", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.mode == "real" and not HAS_PYSERIAL:
        print(
            json.dumps(
                {
                    "passed": False,
                    "error": "pyserial is required for --mode real",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2

    connect_timeout_s = max(0.1, args.connect_timeout_ms / 1000.0)
    kwargs = dict(
        mode=args.mode,
        port=args.port,
        baud=args.baud,
        cycles=max(1, args.cycles),
        threshold=float(args.threshold),
        connect_timeout_s=connect_timeout_s,
        settle_ms=max(0, args.settle_ms),
        inject_drop_every=max(0, args.inject_drop_every),
        fail_open_every=max(0, args.fail_open_every),
    )

    if args.mode == "mock":
        with patch_serial_for_mock(kwargs["fail_open_every"]):
            stats, passed = run_gate(**kwargs)
    else:
        stats, passed = run_gate(**kwargs)

    report = stats.to_dict()
    report["mode"] = args.mode
    report["port"] = args.port
    report["baud"] = args.baud
    report["threshold"] = args.threshold
    report["passed"] = passed
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.json_out:
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
