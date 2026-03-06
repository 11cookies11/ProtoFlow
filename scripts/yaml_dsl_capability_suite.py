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


def _run_script(case_id: str, script_text: str, scenario_name: str = "at_basic.yaml") -> Tuple[Dict[str, Any], Path]:
    out_dir = (ROOT / "runs" / f"dsl_cap_{case_id}_{int(time.time() * 1000)}").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    script_path = out_dir / f"{case_id}.yaml"
    script_path.write_text(script_text, encoding="utf-8")
    ast = parse_script(str(script_path))

    client, server = create_mock_pair()
    scenario = load_scenario(ROOT / "tools" / "target_emulator" / "scenarios" / scenario_name)
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


def _case_foundation() -> Tuple[bool, Dict[str, Any], Path]:
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
security:
  file:
    root_allowlist: ["./tmp", "./runs"]
steps:
  - name: send
    text: "AT"
  - name: sleep
    ms: 10
  - name: expect
    match: { type: contains, pattern: "OK" }
  - name: send
    text: "AT+SN?"
  - name: expect
    match: { type: regex, pattern: "SN:[A-Z0-9]+" }
    capture:
      - var: sn
        regex: "SN:([A-Z0-9]+)"
  - name: assert
    expr: "${sn} != ''"
artifacts:
  dir: "./runs/cap_foundation_${now}"
  raw_log: true
  summary_json: true
  report_csv: true
""".strip()
    summary, out = _run_script("foundation", script)
    ok = bool(summary.get("ok", False)) and str(summary.get("vars", {}).get("sn", "")).startswith("SN")
    return ok, summary, out


def _case_control_flow() -> Tuple[bool, Dict[str, Any], Path]:
    script = """
version: "0.2"
vars:
  ready: false
  last_loop_round: 0
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
security:
  file:
    root_allowlist: ["./tmp", "./runs"]
steps:
  - name: if
    when: "${ready} == False"
    then:
      - name: send
        text: "AT"
      - name: expect
        match: { type: contains, pattern: "OK" }
  - name: loop
    times: 4
    until: "${ready} == True"
    steps:
      - name: if
        when: "${last_loop_round} >= 2"
        then:
          - name: file
            op: write_text
            path: "./tmp/cap_ready.flag"
            content: "1"
          - name: file
            op: exists
            path: "./tmp/cap_ready.flag"
            save_as: ready
      - name: sleep
        ms: 5
  - name: switch_session
    baud: 921600
    dry_run: true
  - name: assert
    expr: "${ready} == True"
artifacts:
  dir: "./runs/cap_control_${now}"
  raw_log: true
  summary_json: true
""".strip()
    summary, out = _run_script("control_flow", script)
    ok = bool(summary.get("ok", False)) and bool(summary.get("vars", {}).get("ready", False))
    return ok, summary, out


def _case_data_plane() -> Tuple[bool, Dict[str, Any], Path]:
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
  - name: parse
    format: json
    source: '{"adc":{"voltage":12.11},"temp":40.1}'
    save_as: p_json
  - name: path
    source: "${p_json}"
    path: "adc.voltage"
    save_as: volt
  - name: parse
    format: kv
    source: "state=ready\\nerr=0"
    save_as: p_kv
  - name: parse
    format: csv
    source: "metric,value\\nrpm,1500\\npwm,42"
    save_as: p_csv
  - name: path
    source: "${p_csv}"
    path: "1.value"
    save_as: pwm
  - name: measure
    metric: voltage
    value: "${volt}"
    unit: V
  - name: assert_range
    value: "${measure.voltage}"
    min: 11.8
    max: 12.3
  - name: assert
    all:
      - expr: "${p_kv.state} == 'ready'"
      - expr: "${pwm} == '42'"
artifacts:
  dir: "./runs/cap_data_${now}"
  raw_log: true
  summary_json: true
""".strip()
    summary, out = _run_script("data_plane", script)
    ok = bool(summary.get("ok", False)) and len(summary.get("vars", {}).get("metrics", [])) >= 1
    return ok, summary, out


def _case_security_deny_exec() -> Tuple[bool, Dict[str, Any], Path]:
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
security:
  exec:
    enabled: false
    allow_commands: ["python"]
    cwd_allowlist: ["."]
steps:
  - name: exec
    command: "python --version"
""".strip()
    summary, out = _run_script("security_deny_exec", script)
    err = summary.get("error") or {}
    ok = (not bool(summary.get("ok", True))) and err.get("code") == "EXEC_NOT_ALLOWED"
    return ok, summary, out


def _case_security_deny_file() -> Tuple[bool, Dict[str, Any], Path]:
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
security:
  file:
    root_allowlist: ["./runs"]
steps:
  - name: file
    op: write_text
    path: "./tmp/deny.txt"
    content: "x"
""".strip()
    summary, out = _run_script("security_deny_file", script)
    err = summary.get("error") or {}
    ok = (not bool(summary.get("ok", True))) and err.get("code") == "FILE_NOT_ALLOWED"
    return ok, summary, out


def main() -> int:
    checks: List[Tuple[str, bool, Dict[str, Any], Path]] = []
    for name, fn in [
        ("dsl.foundation", _case_foundation),
        ("dsl.control_flow", _case_control_flow),
        ("dsl.data_plane", _case_data_plane),
        ("dsl.security_deny_exec", _case_security_deny_exec),
        ("dsl.security_deny_file", _case_security_deny_file),
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
        "suite": "yaml_dsl.capability_suite",
        "ok": overall,
        "generated_at": time.time(),
        "cases": report_cases,
    }
    out = (ROOT / "runs" / "yaml_dsl_capability_suite_report.json").resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"report={out}")
    print(f"RESULT: {'PASSED' if overall else 'FAILED'}")
    return 0 if overall else 2


if __name__ == "__main__":
    raise SystemExit(main())
