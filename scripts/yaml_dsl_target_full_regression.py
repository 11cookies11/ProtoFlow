from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Tuple

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


def _run_case(case_id: str, scenario_file: Path, script_text: str) -> Tuple[Dict[str, Any], Path]:
    case_dir = (ROOT / "runs" / f"target_dsl_{case_id}_{int(time.time() * 1000)}").resolve()
    case_dir.mkdir(parents=True, exist_ok=True)
    script_path = case_dir / f"{case_id}.yaml"
    script_path.write_text(script_text, encoding="utf-8")

    ast = parse_script(str(script_path))
    client, server = create_mock_pair()
    emu = TargetEmulator(
        scenario=load_scenario(scenario_file),
        config=EmulatorConfig(mode="mock", artifacts_dir=str(case_dir / "target_emu")),
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
        return summary, case_dir
    finally:
        try:
            ctx.close()
        except Exception:
            pass
        emu.stop()


def _case_basic() -> Tuple[Dict[str, Any], Path]:
    yaml_text = """
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
  read_timeout_ms: 120

steps:
  - name: send
    text: "AT"
  - name: expect
    match:
      type: contains
      pattern: "OK"
  - name: send
    text: "AT+SN?"
  - name: expect
    match:
      type: regex
      pattern: "SN:[A-Z0-9]+"
    capture:
      - var: dut_sn
        regex: "SN:([A-Z0-9]+)"
        group: 1
  - name: assert
    all:
      - expr: "${dut_sn} != ''"
      - match:
          type: startswith
          pattern: "SN"
        source: "${dut_sn}"

artifacts:
  dir: "./runs/yaml_dsl_target_basic_${now}"
  raw_log: true
  summary_json: true
  report_csv: true
""".strip()
    return _run_case("basic", ROOT / "tools" / "target_emulator" / "scenarios" / "at_basic.yaml", yaml_text)


def _case_retry_upgrade() -> Tuple[Dict[str, Any], Path]:
    yaml_text = """
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
  read_timeout_ms: 120

steps:
  - name: send
    text: "ENTER_BOOT"
  - name: expect
    timeout_ms: 90
    match:
      type: contains
      pattern: "BOOT:READY"
    retry:
      count: 2
      backoff_ms: 30
      strategy: fixed
  - name: send
    text: "FLASH:BEGIN"
  - name: expect
    match:
      type: contains
      pattern: "ACK"
  - name: send
    text: "FLASH:END"
  - name: expect
    match:
      type: contains
      pattern: "CRC:PASS"

artifacts:
  dir: "./runs/yaml_dsl_target_upgrade_${now}"
  raw_log: true
  summary_json: true
""".strip()
    return _run_case(
        "retry_upgrade",
        ROOT / "tools" / "target_emulator" / "scenarios" / "retry_expect_window.yaml",
        yaml_text,
    )


def _case_advanced() -> Tuple[Dict[str, Any], Path]:
    protocols_dir = (ROOT / "protocols").resolve().as_posix()
    yaml_text = f"""
version: "0.2"

params:
  mode: "diagnose"

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
  exec:
    enabled: true
    allow_commands: ["python"]
    cwd_allowlist: ["."]
  file:
    root_allowlist: ["./runs", "./tmp"]

step_templates:
  ping:
    params: [cmd]
    steps:
      - name: send
        text: "${{cmd}}"
      - name: expect
        match:
          type: contains
          pattern: "OK"

steps:
  - template: ping
    args:
      cmd: "AT"

  - name: parse
    format: json
    source: '{{"adc":{{"voltage":12.10}},"temp":40.5}}'
    save_as: parsed

  - name: path
    source: "${{parsed}}"
    path: "adc.voltage"
    save_as: voltage

  - name: measure
    metric: "voltage"
    value: "${{voltage}}"
    unit: "V"

  - name: assert_range
    value: "${{measure.voltage}}"
    min: 11.8
    max: 12.3

  - name: if
    when: "${{mode}} == 'diagnose'"
    then:
      - name: send
        text: "ATI"
      - name: expect
        match:
          type: contains
          pattern: "ProtoFlow-Target"
    else:
      - name: send
        text: "AT"

  - name: loop
    times: 4
    until: "${{ready}} == True"
    steps:
      - name: if
        when: "${{last_loop_round}} >= 2"
        then:
          - name: file
            op: write_text
            path: "./tmp/ready.flag"
            content: "ok=1"
          - name: file
            op: exists
            path: "./tmp/ready.flag"
            save_as: ready
      - name: sleep
        ms: 20

  - name: switch_session
    baud: 921600
    dry_run: true

  - name: protocol.rpc
    protocol: at_command
    packages_dir: "{protocols_dir}"
    request:
      cmd: "AT"
      expect:
        status: ok
        contains: "OK"
    timeout_ms: 1000
    save_as: proto_rsp

  - name: exec
    command: "python --version"
    timeout_ms: 5000
    save_stdout_as: py_out
    save_stderr_as: py_err

  - name: file
    op: write_text
    path: "./tmp/full_reg_report.txt"
    content: "voltage=${{measure.voltage}}\\nproto_ok=${{proto_rsp.ok}}\\npy=${{py_out}}${{py_err}}"

  - name: file
    op: read_text
    path: "./tmp/full_reg_report.txt"
    save_as: report

  - name: assert
    all:
      - expr: "${{report}} != ''"
      - expr: "${{ready}} == True"

artifacts:
  dir: "./runs/yaml_dsl_target_advanced_${{now}}"
  raw_log: true
  summary_json: true
  report_csv: true
""".strip()
    return _run_case("advanced", ROOT / "tools" / "target_emulator" / "scenarios" / "at_basic.yaml", yaml_text)


def main() -> int:
    ok = True
    outputs = []

    summary1, out1 = _case_basic()
    outputs.append(str(out1))
    ok &= _check("case_basic.ok", bool(summary1.get("ok", False)))
    ok &= _check("case_basic.capture_sn", str(summary1.get("vars", {}).get("dut_sn", "")).startswith("SN"))

    summary2, out2 = _case_retry_upgrade()
    outputs.append(str(out2))
    ok &= _check("case_retry_upgrade.ok", bool(summary2.get("ok", False)))
    ok &= _check(
        "case_retry_upgrade.retry_happened",
        any(int(step.get("attempts", 1)) > 1 for step in summary2.get("steps", []) if step.get("name") == "expect"),
    )

    summary3, out3 = _case_advanced()
    outputs.append(str(out3))
    ok &= _check("case_advanced.ok", bool(summary3.get("ok", False)))
    ok &= _check("case_advanced.has_metrics", len(summary3.get("vars", {}).get("metrics", [])) >= 1)
    ok &= _check("case_advanced.protocol_ok", bool(summary3.get("vars", {}).get("proto_rsp", {}).get("ok", False)))

    report = {
        "ok": ok,
        "cases": ["basic", "retry_upgrade", "advanced"],
        "outputs": outputs,
        "ts": time.time(),
    }
    out = (ROOT / "runs" / "yaml_dsl_target_full_regression_report.json").resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"report={out}")
    print(f"RESULT: {'PASSED' if ok else 'FAILED'}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
