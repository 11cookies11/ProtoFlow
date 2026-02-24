from __future__ import annotations

import argparse
import json
import sys
import time
import types
from dataclasses import dataclass
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


@dataclass
class GateResult:
    start_stop_ok: bool = False
    frame_emit_ok: bool = False
    channel_filter_ok: bool = False
    frame_count: int = 0
    errors: List[str] | None = None

    def to_dict(self) -> Dict[str, Any]:
        errors = self.errors or []
        passed = self.start_stop_ok and self.frame_emit_ok and self.channel_filter_ok and not errors
        return {
            "passed": passed,
            "start_stop_ok": self.start_stop_ok,
            "frame_emit_ok": self.frame_emit_ok,
            "channel_filter_ok": self.channel_filter_ok,
            "frame_count": self.frame_count,
            "errors": errors,
        }


def wait_until(predicate, timeout_s: float = 1.0, interval_s: float = 0.02) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(interval_s)
    return False


def run_gate() -> GateResult:
    bus = EventBus()
    result = GateResult(errors=[])
    frames: List[Dict[str, Any]] = []
    PacketAnalysisEngine(bus)

    def on_frame(payload: Any) -> None:
        if isinstance(payload, dict):
            frames.append(payload)

    bus.subscribe("capture.frame", on_frame)
    bus.publish("comm.connected", {"type": "serial", "port": "COM5", "baud": 115200})

    # Scenario 1: start capture and ensure RX/TX frames are emitted.
    bus.publish("capture.control", {"action": "start", "channel": "COM5"})
    bus.publish("comm.tx", bytes.fromhex("01 03 00 00 00 01 84 0A"))
    bus.publish("comm.rx", bytes.fromhex("01 03 02 00 2A 39 9B"))
    if wait_until(lambda: len(frames) >= 2, timeout_s=1.5):
        result.frame_emit_ok = True
    else:
        result.errors.append("capture.frame not emitted for RX/TX after start")

    # Scenario 2: stop capture and ensure frames no longer grow.
    before_stop = len(frames)
    bus.publish("capture.control", {"action": "stop"})
    bus.publish("comm.tx", b"\x01\x03")
    time.sleep(0.2)
    after_stop = len(frames)
    if after_stop == before_stop:
        result.start_stop_ok = True
    else:
        result.errors.append("capture.frame still emitted after stop")

    # Scenario 3: channel filter mismatch should block frames.
    frames.clear()
    bus.publish("capture.control", {"action": "start", "channel": "COM7"})
    bus.publish("comm.tx", bytes.fromhex("01 03 00 00"))
    time.sleep(0.2)
    bus.publish("capture.control", {"action": "stop"})
    if len(frames) == 0:
        result.channel_filter_ok = True
    else:
        result.errors.append("channel filter mismatch did not block capture frame")

    result.frame_count = len(frames)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture pipeline gate for W4-02")
    parser.add_argument("--json-out", default="", help="Write JSON result to file")
    args = parser.parse_args()

    result = run_gate().to_dict()
    output = json.dumps(result, ensure_ascii=False, indent=2)
    print(output)
    if args.json_out:
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output, encoding="utf-8")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
