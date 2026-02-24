from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]


def run_cmd(args: list[str], cwd: Path) -> tuple[int, str]:
    proc = subprocess.run(args, cwd=str(cwd), capture_output=True, text=True)
    output = (proc.stdout or "") + (("\n" + proc.stderr) if proc.stderr else "")
    return int(proc.returncode), output.strip()


def run_core_gate(*, out_dir: Path, serial_cycles: int, serial_mode: str) -> Dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)

    steps = [
        (
            "w4_gate_runner",
            [
                sys.executable,
                "scripts/w4_gate_runner.py",
                "--serial-mode",
                serial_mode,
                "--serial-cycles",
                str(serial_cycles),
                "--out-dir",
                str(out_dir),
            ],
        ),
        ("dsl_lifecycle_gate", [sys.executable, "scripts/dsl_lifecycle_gate.py"]),
        ("protocol_replay_gate", [sys.executable, "scripts/protocol_replay_gate.py"]),
        ("proxy_monitor_gate", [sys.executable, "scripts/proxy_monitor_gate.py"]),
    ]

    details = []
    all_passed = True
    for name, cmd in steps:
        code, output = run_cmd(cmd, ROOT)
        step_passed = code == 0
        all_passed = all_passed and step_passed
        details.append(
            {
                "name": name,
                "passed": step_passed,
                "exit_code": code,
                "command": cmd,
                "output_preview": output[-2000:] if output else "",
            }
        )

    report = {
        "passed": all_passed,
        "serial_mode": serial_mode,
        "serial_cycles": serial_cycles,
        "steps": details,
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Core regression gate (W7-01)")
    parser.add_argument("--out-dir", default="artifacts/core_regression")
    parser.add_argument("--serial-cycles", type=int, default=50)
    parser.add_argument("--serial-mode", choices=["mock", "real"], default="mock")
    args = parser.parse_args()

    out_dir = ROOT / args.out_dir
    report = run_core_gate(
        out_dir=out_dir,
        serial_cycles=max(1, args.serial_cycles),
        serial_mode=args.serial_mode,
    )

    summary_path = out_dir / "core_regression_summary.json"
    summary_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
