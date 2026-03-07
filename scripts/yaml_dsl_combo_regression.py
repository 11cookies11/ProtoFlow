from __future__ import annotations

import json
import sys
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


def _run_case(script_text: str) -> Tuple[Dict[str, Any], Path]:
    out_dir = (ROOT / "runs" / f"yaml_dsl_combo_{int(time.time() * 1000)}").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    script_path = out_dir / "combo_case.yaml"
    script_path.write_text(script_text, encoding="utf-8")
    ast = parse_script(str(script_path))

    client, server = create_mock_pair()
    scenario = load_scenario(ROOT / "tools" / "target_emulator" / "scenarios" / "combo_upgrade_config.yaml")
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


def main() -> int:
    script = """
version: "0.2"

params:
  sn: "SN90001"
  fw_ver: "1.2.3"

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

security:
  file:
    root_allowlist: ["./tmp", "./runs"]

steps:
  - name: send
    text: "ENTER_BOOT"
  - name: expect
    timeout_ms: 120
    match: { type: contains, pattern: "BOOT:READY" }
    retry:
      count: 2
      backoff_ms: 40
      strategy: fixed
  - name: send
    text: "FLASH:BEGIN"
  - name: expect
    match: { type: contains, pattern: "ACK" }
  - name: send
    text: "FLASH:END"
  - name: expect
    match: { type: contains, pattern: "CRC:PASS" }
  - name: send
    text: "SET:SN=${params.sn}"
  - name: expect
    match: { type: contains, pattern: "WRITE:OK" }
  - name: send
    text: "GET:SN?"
  - name: expect
    match: { type: regex, pattern: "SN:[A-Z0-9]+" }
    capture:
      - var: read_sn
        regex: "SN:([A-Z0-9]+)"
  - name: send
    text: "GET:VER?"
  - name: expect
    match: { type: regex, pattern: "VER:[0-9.]+" }
    capture:
      - var: read_ver
        regex: "VER:([0-9.]+)"
  - name: assert
    all:
      - expr: "${read_sn} == ${params.sn}"
      - expr: "${read_ver} == ${params.fw_ver}"
  - name: file
    op: write_text
    path: "./tmp/combo_report.txt"
    content: "sn=${read_sn}\\nver=${read_ver}\\nflash=CRC:PASS"
  - name: file
    op: read_text
    path: "./tmp/combo_report.txt"
    save_as: combo_report
  - name: assert
    expr: "${combo_report} != ''"

artifacts:
  dir: "./runs/yaml_dsl_combo_${now}"
  raw_log: true
  summary_json: true
  report_csv: true
""".strip()

    summary, out_dir = _run_case(script)
    ok = bool(summary.get("ok", False))
    vars_block = summary.get("vars", {})
    steps = summary.get("steps", [])
    retry_hit = any(int(s.get("attempts", 1)) > 1 for s in steps if s.get("name") == "expect")

    ok &= _check("combo.ok", bool(summary.get("ok", False)))
    ok &= _check("combo.sn_match", str(vars_block.get("read_sn", "")) == "SN90001")
    ok &= _check("combo.ver_match", str(vars_block.get("read_ver", "")) == "1.2.3")
    ok &= _check("combo.retry_hit", retry_hit)

    report = {
        "suite": "yaml_dsl.combo_regression",
        "ok": ok,
        "output_dir": str(out_dir),
        "elapsed_ms": int(summary.get("elapsed_ms", 0)),
        "read_sn": vars_block.get("read_sn"),
        "read_ver": vars_block.get("read_ver"),
        "retry_hit": retry_hit,
        "generated_at": time.time(),
    }
    report_path = (ROOT / "runs" / "yaml_dsl_combo_regression_report.json").resolve()
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"report={report_path}")
    print(f"RESULT: {'PASSED' if ok else 'FAILED'}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
