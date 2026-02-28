from __future__ import annotations

import argparse
import json
import os
import queue
import statistics
import sys
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

try:
    import serial
except Exception:  # pragma: no cover
    serial = None  # type: ignore[assignment]

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from infra.common.event_bus import EventBus
from infra.comm.proxy_forward_manager import ProxyForwardManager


@dataclass
class CaseResult:
    name: str
    passed: bool
    details: str = ""
    samples_ms: List[float] = field(default_factory=list)


def _now() -> float:
    return time.perf_counter()


def _drain_serial(ser: serial.Serial) -> None:
    end = time.time() + 0.2
    while time.time() < end:
        waiting = ser.in_waiting if ser.is_open else 0
        if waiting <= 0:
            break
        ser.read(waiting)


def _await_bytes(ser: serial.Serial, expected_len: int, timeout_sec: float) -> bytes:
    deadline = time.time() + timeout_sec
    chunks = bytearray()
    while time.time() < deadline:
        waiting = ser.in_waiting if ser.is_open else 0
        if waiting > 0:
            chunks.extend(ser.read(waiting))
            if len(chunks) >= expected_len:
                return bytes(chunks)
        time.sleep(0.005)
    return bytes(chunks)


def _await_event(
    q: "queue.Queue[Dict[str, Any]]",
    pair_id: str,
    expected_src_role: str,
    timeout_sec: float,
) -> Optional[Dict[str, Any]]:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        wait_left = max(0.01, deadline - time.time())
        try:
            item = q.get(timeout=wait_left)
        except queue.Empty:
            continue
        if not isinstance(item, dict):
            continue
        if str(item.get("pair_id")) != pair_id:
            continue
        if str(item.get("src_role") or "").lower() != expected_src_role:
            continue
        return item
    return None


def _roundtrip_once(
    write_ser: serial.Serial,
    read_ser: serial.Serial,
    payload: bytes,
    timeout_sec: float,
) -> tuple[bool, str, float]:
    _drain_serial(write_ser)
    _drain_serial(read_ser)
    t0 = _now()
    write_ser.write(payload)
    got = _await_bytes(read_ser, len(payload), timeout_sec)
    elapsed_ms = (_now() - t0) * 1000.0
    if got != payload:
        return False, f"payload mismatch: expect={payload.hex()} got={got.hex()}", elapsed_ms
    return True, "ok", elapsed_ms


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Proxy forwarding regression for real/virtual serial devices.",
    )
    parser.add_argument("--host-port", required=True, help="Port opened by proxy as host side.")
    parser.add_argument("--device-port", required=True, help="Port opened by proxy as device side.")
    parser.add_argument(
        "--test-host-port",
        required=True,
        help="Peer port used by tester to inject/read host-side traffic.",
    )
    parser.add_argument(
        "--test-device-port",
        required=True,
        help="Peer port used by tester to inject/read device-side traffic.",
    )
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--data-bits", default="8", choices=["5", "6", "7", "8"])
    parser.add_argument("--stop-bits", default="1", choices=["1", "1.5", "2"])
    parser.add_argument("--parity", default="none", choices=["none", "even", "odd", "mark", "space"])
    parser.add_argument("--flow-control", default="none", choices=["none", "rtscts", "xonxoff"])
    parser.add_argument("--iterations", type=int, default=20, help="Count for each direction.")
    parser.add_argument("--payload-size", type=int, default=64, help="Bytes per case.")
    parser.add_argument("--timeout-sec", type=float, default=2.0)
    parser.add_argument("--soak-sec", type=int, default=0, help="Optional long-run stress duration.")
    parser.add_argument("--json-out", default="", help="Optional path to save machine-readable report.")
    args = parser.parse_args()
    if serial is None:
        print("pyserial is required. Install with: pip install -r requirements.txt")
        return 2

    pair_id = f"proxy-regression-{int(time.time())}"
    bus = EventBus()
    manager = ProxyForwardManager(bus)
    data_events: "queue.Queue[Dict[str, Any]]" = queue.Queue()
    status_events: "queue.Queue[Dict[str, Any]]" = queue.Queue()
    bus.subscribe("proxy.data", lambda payload: data_events.put(payload if isinstance(payload, dict) else {}))
    bus.subscribe("proxy.status", lambda payload: status_events.put(payload if isinstance(payload, dict) else {}))

    cfg: Dict[str, Any] = {
        "hostPort": args.host_port,
        "devicePort": args.device_port,
        "baud": args.baud,
        "dataBits": args.data_bits,
        "stopBits": args.stop_bits,
        "parity": args.parity,
        "flowControl": args.flow_control,
    }

    report: Dict[str, Any] = {
        "pair_id": pair_id,
        "ports": {
            "host_port": args.host_port,
            "device_port": args.device_port,
            "test_host_port": args.test_host_port,
            "test_device_port": args.test_device_port,
        },
        "settings": {
            "baud": args.baud,
            "data_bits": args.data_bits,
            "stop_bits": args.stop_bits,
            "parity": args.parity,
            "flow_control": args.flow_control,
            "iterations": args.iterations,
            "payload_size": args.payload_size,
            "timeout_sec": args.timeout_sec,
            "soak_sec": args.soak_sec,
        },
        "results": [],
        "status": "failed",
    }

    results: List[CaseResult] = []
    test_host: Optional[serial.Serial] = None
    test_device: Optional[serial.Serial] = None
    started = manager.start_pair(pair_id, cfg)
    if not started.ok:
        results.append(CaseResult("start_pair", False, started.error))
        report["results"] = [r.__dict__ for r in results]
        if args.json_out:
            with open(args.json_out, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"[FAIL] start_pair: {started.error}")
        return 2

    try:
        test_host = serial.Serial(args.test_host_port, args.baud, timeout=0.1, write_timeout=0.5)
        test_device = serial.Serial(args.test_device_port, args.baud, timeout=0.1, write_timeout=0.5)

        running_seen = False
        end_status_wait = time.time() + 2.0
        while time.time() < end_status_wait:
            try:
                evt = status_events.get(timeout=0.2)
            except queue.Empty:
                continue
            if evt.get("pair_id") == pair_id and evt.get("status") == "running":
                running_seen = True
                break
        results.append(CaseResult("status.running", running_seen, "" if running_seen else "no running status event"))

        h2d_samples: List[float] = []
        h2d_ok = True
        h2d_msg = "ok"
        for _ in range(max(1, args.iterations)):
            payload = os.urandom(max(1, args.payload_size))
            ok, msg, elapsed = _roundtrip_once(test_host, test_device, payload, args.timeout_sec)
            if not ok:
                h2d_ok = False
                h2d_msg = msg
                break
            evt = _await_event(data_events, pair_id, "host", args.timeout_sec)
            if evt is None:
                h2d_ok = False
                h2d_msg = "missing proxy.data event for host direction"
                break
            h2d_samples.append(elapsed)
        results.append(CaseResult("host_to_device.forward", h2d_ok, h2d_msg, h2d_samples))

        d2h_samples: List[float] = []
        d2h_ok = True
        d2h_msg = "ok"
        for _ in range(max(1, args.iterations)):
            payload = os.urandom(max(1, args.payload_size))
            ok, msg, elapsed = _roundtrip_once(test_device, test_host, payload, args.timeout_sec)
            if not ok:
                d2h_ok = False
                d2h_msg = msg
                break
            evt = _await_event(data_events, pair_id, "device", args.timeout_sec)
            if evt is None:
                d2h_ok = False
                d2h_msg = "missing proxy.data event for device direction"
                break
            d2h_samples.append(elapsed)
        results.append(CaseResult("device_to_host.forward", d2h_ok, d2h_msg, d2h_samples))

        if args.soak_sec > 0 and h2d_ok and d2h_ok:
            soak_end = time.time() + args.soak_sec
            soak_samples: List[float] = []
            soak_ok = True
            soak_msg = "ok"
            toggle = True
            while time.time() < soak_end:
                payload = os.urandom(16)
                if toggle:
                    ok, msg, elapsed = _roundtrip_once(test_host, test_device, payload, args.timeout_sec)
                    if ok:
                        evt = _await_event(data_events, pair_id, "host", args.timeout_sec)
                        ok = evt is not None
                        if not ok:
                            msg = "missing proxy.data event during soak(host)"
                else:
                    ok, msg, elapsed = _roundtrip_once(test_device, test_host, payload, args.timeout_sec)
                    if ok:
                        evt = _await_event(data_events, pair_id, "device", args.timeout_sec)
                        ok = evt is not None
                        if not ok:
                            msg = "missing proxy.data event during soak(device)"
                if not ok:
                    soak_ok = False
                    soak_msg = msg
                    break
                soak_samples.append(elapsed)
                toggle = not toggle
                time.sleep(0.02)
            results.append(CaseResult("soak.forwarding", soak_ok, soak_msg, soak_samples))

    except Exception as exc:
        results.append(CaseResult("runtime", False, str(exc)))
    finally:
        if test_host is not None:
            try:
                test_host.close()
            except Exception:
                pass
        if test_device is not None:
            try:
                test_device.close()
            except Exception:
                pass
        manager.stop_pair(pair_id)

    passed = all(r.passed for r in results)
    report["status"] = "passed" if passed else "failed"
    report["results"] = []
    for item in results:
        row: Dict[str, Any] = {
            "name": item.name,
            "passed": item.passed,
            "details": item.details,
        }
        if item.samples_ms:
            row["latency_ms"] = {
                "count": len(item.samples_ms),
                "avg": round(statistics.mean(item.samples_ms), 3),
                "p95": round(sorted(item.samples_ms)[max(0, int(len(item.samples_ms) * 0.95) - 1)], 3),
                "max": round(max(item.samples_ms), 3),
            }
        report["results"].append(row)

    for row in report["results"]:
        mark = "PASS" if row["passed"] else "FAIL"
        line = f"[{mark}] {row['name']}"
        if row.get("latency_ms"):
            latency = row["latency_ms"]
            line += f" avg={latency['avg']}ms p95={latency['p95']}ms max={latency['max']}ms"
        if row.get("details"):
            line += f" | {row['details']}"
        print(line)
    print(f"RESULT: {report['status'].upper()}")

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"report saved: {args.json_out}")

    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
