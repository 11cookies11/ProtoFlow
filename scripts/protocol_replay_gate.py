from __future__ import annotations

import json
import sys
import time
import types
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Minimal yaml stub for environments without PyYAML.
if "yaml" not in sys.modules:
    yaml_stub = types.ModuleType("yaml")
    yaml_stub.safe_load = lambda *_args, **_kwargs: {}
    sys.modules["yaml"] = yaml_stub

from app.packet_engine import PacketAnalysisEngine
from infra.common.event_bus import EventBus


def wait_until(predicate, timeout_s: float = 1.0, interval_s: float = 0.02) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(interval_s)
    return False


def run_gate() -> Dict[str, Any]:
    bus = EventBus()
    PacketAnalysisEngine(bus)
    frames: List[Dict[str, Any]] = []
    bus.subscribe("capture.frame", lambda payload: frames.append(payload) if isinstance(payload, dict) else None)

    bus.publish("comm.connected", {"type": "serial", "port": "COM5", "baud": 115200})
    bus.publish("capture.control", {"action": "start", "channel": "COM5"})

    # Valid Modbus request/response + exception response
    samples = [
        bytes.fromhex("01 03 00 00 00 01 84 0A"),
        bytes.fromhex("01 03 02 00 2A 39 9B"),
        bytes.fromhex("01 83 02 C0 F1"),
        bytes.fromhex("AA BB CC DD"),  # unknown sample
    ]
    for raw in samples:
        bus.publish("comm.rx", raw)
    wait_until(lambda: len(frames) >= len(samples), timeout_s=1.5)
    bus.publish("capture.control", {"action": "stop"})

    modbus = [f for f in frames if (f.get("protocol") or {}).get("name") == "Modbus RTU"]
    unknown = [f for f in frames if (f.get("protocol") or {}).get("name") == "Unknown"]
    exception_frames = [f for f in modbus if "exception=" in str(f.get("summary") or "")]
    report = {
        "total_frames": len(frames),
        "modbus_frames": len(modbus),
        "unknown_frames": len(unknown),
        "exception_frames": len(exception_frames),
        "passed": (
            len(frames) >= len(samples)
            and len(modbus) >= 3
            and len(unknown) >= 1
            and len(exception_frames) >= 1
        ),
    }
    return report


def main() -> int:
    report = run_gate()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
