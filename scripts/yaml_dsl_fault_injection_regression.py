from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dsl_runtime.engine.context import RuntimeContext
from dsl_runtime.engine.v01_artifacts import export_v01_artifacts
from dsl_runtime.engine.v01_executor import execute_v01
from dsl_runtime.lang.parser import parse_script
from tools.target_emulator import EmulatorConfig, TargetEmulator, load_scenario
from tools.target_emulator.transport import create_mock_pair


def _check(name: str, cond: bool) -> bool:
    print(f"[{'PASS' if cond else 'FAIL'}] {name}")
    return cond


def _run_script(case_id: str, script_text: str) -> Tuple[Dict[str, Any], Path]:
    out_dir = (ROOT / "runs" / f"dsl_fault_{case_id}_{int(time.time() * 1000)}").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    script_path = out_dir / f"{case_id}.yaml"
    script_path.write_text(script_text, encoding="utf-8")
    ast = parse_script(str(script_path))

    client, server = create_mock_pair()
    scenario = load_scenario(ROOT / "tools" / "target_emulator" / "scenarios" / "fault_injection_matrix.yaml")
    emu = TargetEmulator(
        scenario=scenario,
        config=EmulatorConfig(mode="mock", artifacts_dir=str(out_dir / "target")),
        endpoint=server,
    )
    ctx = RuntimeContext(
        channels={"default": client},
        default_channel="default",
        vars_init=dict(ast.vars or {}),
        params_init=dict(ast.params or {}),
        script_path=str(script_path),
        script_text=script_text,
    )
    emu.start()
    try:
        summary = execute_v01(ast, ctx)
        export_v01_artifacts(ast, summary)
    finally:
        ctx.close()
        emu.stop()
    return summary, out_dir


def _case_fault_pass() -> Tuple[bool, Dict[str, Any], Path]:
    script = """
version: "0.2"
session:
  transport: serial
  port: "COM_TEST"
  baud: 115200
  data_bits: 8
  parity: none
  stop_bits: 1
  encoding: ascii
  eol: crlf
  open_timeout_ms: 1000
  read_timeout_ms: 100
steps:
  - name: send
    text: "PING:JITTER"
  - name: expect
    match: { type: contains, pattern: "PONG:JITTER" }
    timeout_ms: 900
  - name: send
    text: "PING:CHUNK"
  - name: expect
    match: { type: regex, pattern: "PAYLOAD:[A-Z]+" }
    timeout_ms: 900
    capture:
      - var: payload
        regex: "PAYLOAD:([A-Z]+)"
  - name: send
    text: "PING:REORDER"
  - name: expect
    match: { type: contains, pattern: "SEQ:2,1" }
    timeout_ms: 500
  - name: assert
    expr: "${payload} != ''"
artifacts:
  dir: "./runs/dsl_fault_pass_${now}"
  raw_log: true
  summary_json: true
""".strip()
    summary, out = _run_script("pass", script)
    ok = bool(summary.get("ok", False)) and str(summary.get("vars", {}).get("payload", "")) != ""
    return ok, summary, out


def _case_timeout_fail() -> Tuple[bool, Dict[str, Any], Path]:
    script = """
version: "0.2"
session:
  transport: serial
  port: "COM_TEST"
  baud: 115200
  data_bits: 8
  parity: none
  stop_bits: 1
  encoding: ascii
  eol: crlf
  open_timeout_ms: 1000
  read_timeout_ms: 100
steps:
  - name: send
    text: "PING:TIMEOUT"
  - name: expect
    match: { type: contains, pattern: "SHOULD_NOT_ARRIVE" }
    timeout_ms: 180
""".strip()
    summary, out = _run_script("timeout_fail", script)
    err = summary.get("error") or {}
    ok = (not bool(summary.get("ok", True))) and err.get("code") == "STEP_TIMEOUT"
    return ok, summary, out


def _case_close_pass() -> Tuple[bool, Dict[str, Any], Path]:
    script = """
version: "0.2"
session:
  transport: serial
  port: "COM_TEST"
  baud: 115200
  data_bits: 8
  parity: none
  stop_bits: 1
  encoding: ascii
  eol: crlf
  open_timeout_ms: 1000
  read_timeout_ms: 100
steps:
  - name: send
    text: "PING:CLOSE"
  - name: expect
    match: { type: contains, pattern: "BYE" }
    timeout_ms: 500
""".strip()
    summary, out = _run_script("close_pass", script)
    ok = bool(summary.get("ok", False))
    return ok, summary, out


def main() -> int:
    checks: List[Tuple[str, bool, Dict[str, Any], Path]] = []
    for name, fn in [
        ("dsl_fault.pass_path", _case_fault_pass),
        ("dsl_fault.timeout_fail", _case_timeout_fail),
        ("dsl_fault.close_pass", _case_close_pass),
    ]:
        ok, summary, out = fn()
        checks.append((name, ok, summary, out))
        _check(name, ok)

    overall = all(item[1] for item in checks)
    report_cases = []
    for name, ok, summary, out in checks:
        report_cases.append(
            {
                "id": name,
                "ok": ok,
                "elapsed_ms": int(summary.get("elapsed_ms", 0)),
                "error_code": (summary.get("error") or {}).get("code"),
                "error_message": (summary.get("error") or {}).get("message"),
                "logs": [str(out / "summary.json"), str(out / "raw_log.jsonl")],
            }
        )
    report = {
        "suite": "yaml_dsl.fault_injection_regression",
        "ok": overall,
        "generated_at": time.time(),
        "cases": report_cases,
    }
    out = (ROOT / "runs" / "yaml_dsl_fault_injection_regression_report.json").resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"report={out}")
    print(f"RESULT: {'PASSED' if overall else 'FAILED'}")
    return 0 if overall else 2


if __name__ == "__main__":
    raise SystemExit(main())
