from __future__ import annotations

import argparse
import json
import statistics
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


def _p95(samples: List[float]) -> float:
    if not samples:
        return 0.0
    ordered = sorted(samples)
    idx = max(0, int(len(ordered) * 0.95) - 1)
    return float(ordered[idx])


def _count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for _ in handle)


def _run_case(case_id: str, scenario_name: str, script_text: str) -> Tuple[Dict[str, Any], Path]:
    out_dir = (ROOT / "runs" / f"yaml_dsl_perf_{case_id}_{int(time.time() * 1000)}").resolve()
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


def _run_basic() -> Tuple[Dict[str, Any], Path]:
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
  read_timeout_ms: 120
steps:
  - name: send
    text: "AT"
  - name: expect
    match: { type: contains, pattern: "OK" }
artifacts:
  dir: "./runs/yaml_dsl_perf_basic_${now}"
  raw_log: true
  summary_json: true
""".strip()
    return _run_case("basic", "at_basic.yaml", script)


def _run_retry() -> Tuple[Dict[str, Any], Path]:
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
  read_timeout_ms: 120
steps:
  - name: send
    text: "ENTER_BOOT"
  - name: expect
    timeout_ms: 90
    match: { type: contains, pattern: "BOOT:READY" }
    retry:
      count: 2
      backoff_ms: 30
      strategy: fixed
artifacts:
  dir: "./runs/yaml_dsl_perf_retry_${now}"
  raw_log: true
  summary_json: true
""".strip()
    return _run_case("retry", "retry_expect_window.yaml", script)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run YAML-DSL performance baseline.")
    parser.add_argument("--basic-iters", type=int, default=12)
    parser.add_argument("--retry-iters", type=int, default=8)
    args = parser.parse_args()

    basic_iters = max(1, int(args.basic_iters))
    retry_iters = max(1, int(args.retry_iters))

    basic_elapsed: List[float] = []
    retry_elapsed: List[float] = []
    retry_attempts: List[int] = []
    total_raw_lines = 0
    total_elapsed_ms = 0.0
    failures = 0

    for _ in range(basic_iters):
        summary, out_dir = _run_basic()
        if not summary.get("ok", False):
            failures += 1
        elapsed = float(summary.get("elapsed_ms", 0))
        basic_elapsed.append(elapsed)
        total_elapsed_ms += elapsed
        total_raw_lines += _count_lines(out_dir / "target" / "raw_log.jsonl")

    for _ in range(retry_iters):
        summary, out_dir = _run_retry()
        if not summary.get("ok", False):
            failures += 1
        elapsed = float(summary.get("elapsed_ms", 0))
        retry_elapsed.append(elapsed)
        total_elapsed_ms += elapsed
        total_raw_lines += _count_lines(out_dir / "target" / "raw_log.jsonl")
        for step in summary.get("steps", []):
            if step.get("name") == "expect":
                retry_attempts.append(int(step.get("attempts", 1)))

    basic_avg = statistics.mean(basic_elapsed) if basic_elapsed else 0.0
    retry_avg = statistics.mean(retry_elapsed) if retry_elapsed else 0.0
    retry_cost_ms = retry_avg - basic_avg
    throughput = total_raw_lines / max(0.001, total_elapsed_ms / 1000.0)
    retry_hit_rate = 0.0
    if retry_attempts:
        retry_hit_rate = sum(1 for x in retry_attempts if x > 1) / len(retry_attempts)

    ok = failures == 0 and basic_avg > 0 and retry_avg > 0 and throughput > 0
    report = {
        "suite": "yaml_dsl.performance_baseline",
        "ok": ok,
        "iterations": {"basic": basic_iters, "retry": retry_iters},
        "failures": failures,
        "latency_ms": {
            "basic_avg": round(basic_avg, 3),
            "basic_p95": round(_p95(basic_elapsed), 3),
            "retry_avg": round(retry_avg, 3),
            "retry_p95": round(_p95(retry_elapsed), 3),
            "retry_cost_avg": round(retry_cost_ms, 3),
        },
        "retry": {
            "attempt_samples": retry_attempts,
            "hit_rate": round(retry_hit_rate, 4),
        },
        "log_throughput_lines_per_sec": round(throughput, 3),
        "generated_at": time.time(),
    }

    out_json = (ROOT / "runs" / "yaml_dsl_performance_baseline_report.json").resolve()
    out_md = (ROOT / "runs" / "yaml_dsl_performance_baseline_report.md").resolve()
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(
        "\n".join(
            [
                "# YAML-DSL Performance Baseline",
                f"- ok: {report['ok']}",
                f"- basic iterations: {basic_iters}",
                f"- retry iterations: {retry_iters}",
                f"- basic avg(ms): {report['latency_ms']['basic_avg']}",
                f"- basic p95(ms): {report['latency_ms']['basic_p95']}",
                f"- retry avg(ms): {report['latency_ms']['retry_avg']}",
                f"- retry p95(ms): {report['latency_ms']['retry_p95']}",
                f"- retry avg cost(ms): {report['latency_ms']['retry_cost_avg']}",
                f"- retry hit rate: {report['retry']['hit_rate']}",
                f"- log throughput(lines/s): {report['log_throughput_lines_per_sec']}",
            ]
        ),
        encoding="utf-8",
    )

    print(f"[{'PASS' if failures == 0 else 'FAIL'}] perf.failures")
    print(f"[{'PASS' if throughput > 0 else 'FAIL'}] perf.log_throughput")
    print(f"report_json={out_json}")
    print(f"report_md={out_md}")
    print(f"RESULT: {'PASSED' if ok else 'FAILED'}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
