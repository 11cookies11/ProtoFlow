from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]


def run_cmd(args: list[str], cwd: Path) -> int:
    completed = subprocess.run(args, cwd=str(cwd))
    return int(completed.returncode)


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"passed": False, "error": f"missing report: {path}"}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"passed": False, "error": f"invalid report {path}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run W4 gates and aggregate report")
    parser.add_argument("--serial-mode", choices=["mock", "real"], default="mock")
    parser.add_argument("--serial-port", default="COM5")
    parser.add_argument("--serial-baud", type=int, default=115200)
    parser.add_argument("--serial-cycles", type=int, default=200)
    parser.add_argument("--serial-threshold", type=float, default=99.0)
    parser.add_argument("--out-dir", default="artifacts")
    args = parser.parse_args()

    out_dir = ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    serial_json = out_dir / "w4_serial_gate.json"
    capture_json = out_dir / "w4_capture_gate.json"
    summary_json = out_dir / "w4_gate_summary.json"

    serial_cmd = [
        sys.executable,
        "scripts/serial_reliability_gate.py",
        "--mode",
        args.serial_mode,
        "--port",
        args.serial_port,
        "--baud",
        str(args.serial_baud),
        "--cycles",
        str(args.serial_cycles),
        "--threshold",
        str(args.serial_threshold),
        "--json-out",
        str(serial_json),
    ]
    capture_cmd = [
        sys.executable,
        "scripts/capture_pipeline_gate.py",
        "--json-out",
        str(capture_json),
    ]

    serial_rc = run_cmd(serial_cmd, ROOT)
    capture_rc = run_cmd(capture_cmd, ROOT)
    serial_report = load_json(serial_json)
    capture_report = load_json(capture_json)

    summary = {
        "passed": (serial_rc == 0 and capture_rc == 0 and bool(serial_report.get("passed")) and bool(capture_report.get("passed"))),
        "serial_gate": {
            "exit_code": serial_rc,
            "report": serial_report,
        },
        "capture_gate": {
            "exit_code": capture_rc,
            "report": capture_report,
        },
    }
    summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
