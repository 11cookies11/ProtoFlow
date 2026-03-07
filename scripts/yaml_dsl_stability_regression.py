from __future__ import annotations

import argparse
import gc
import json
import statistics
import sys
import time
import tracemalloc
from pathlib import Path
from typing import Dict, List, Tuple

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


def _run_once(iter_idx: int) -> Tuple[bool, int, str]:
    out_dir = (ROOT / "runs" / f"yaml_dsl_stability_case_{iter_idx}_{int(time.time() * 1000)}").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    script_text = """
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
    text: "AT+SN?"
  - name: expect
    match: { type: regex, pattern: "SN:[A-Z0-9]+" }
    capture:
      - var: sn
        regex: "SN:([A-Z0-9]+)"
  - name: assert
    expr: "${sn} == 'SN00123'"
artifacts:
  dir: "./runs/yaml_dsl_stability_${now}"
  raw_log: true
  summary_json: true
""".strip()
    script_path = out_dir / "stability_case.yaml"
    script_path.write_text(script_text, encoding="utf-8")
    ast = parse_script(str(script_path))

    client, server = create_mock_pair()
    scenario = load_scenario(ROOT / "tools" / "target_emulator" / "scenarios" / "at_basic.yaml")
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

    ok = bool(summary.get("ok", False))
    elapsed_ms = int(summary.get("elapsed_ms", 0))
    sn = str(summary.get("vars", {}).get("sn", ""))
    return ok, elapsed_ms, sn


def main() -> int:
    parser = argparse.ArgumentParser(description="Run YAML-DSL stability regression.")
    parser.add_argument("--iterations", type=int, default=20)
    parser.add_argument("--mem-delta-kb-max", type=int, default=10240)
    args = parser.parse_args()

    iterations = max(1, int(args.iterations))
    mem_delta_kb_max = max(1, int(args.mem_delta_kb_max))

    tracemalloc.start()
    gc.collect()
    mem_start = tracemalloc.get_traced_memory()[0]
    started = time.time()

    elapsed_samples: List[float] = []
    sn_values: List[str] = []
    failures = 0
    for i in range(iterations):
        ok, elapsed_ms, sn = _run_once(i + 1)
        if not ok:
            failures += 1
        elapsed_samples.append(float(elapsed_ms))
        sn_values.append(sn)

    gc.collect()
    mem_end, mem_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    duration_sec = max(0.001, time.time() - started)
    success_rate = (iterations - failures) / iterations
    sn_consistent = len(set(sn_values)) == 1
    mem_delta_kb = (mem_end - mem_start) / 1024.0
    ok = failures == 0 and sn_consistent and mem_delta_kb <= mem_delta_kb_max

    report: Dict[str, object] = {
        "suite": "yaml_dsl.stability_regression",
        "ok": ok,
        "iterations": iterations,
        "failures": failures,
        "success_rate": round(success_rate, 4),
        "sn_consistent": sn_consistent,
        "sn_unique_count": len(set(sn_values)),
        "latency_ms": {
            "avg": round(statistics.mean(elapsed_samples), 3) if elapsed_samples else 0.0,
            "p95": round(_p95(elapsed_samples), 3),
            "max": round(max(elapsed_samples) if elapsed_samples else 0.0, 3),
        },
        "memory_kb": {
            "start": round(mem_start / 1024.0, 3),
            "end": round(mem_end / 1024.0, 3),
            "peak": round(mem_peak / 1024.0, 3),
            "delta": round(mem_delta_kb, 3),
            "delta_limit": mem_delta_kb_max,
        },
        "duration_sec": round(duration_sec, 3),
        "generated_at": time.time(),
    }
    report_path = (ROOT / "runs" / "yaml_dsl_stability_regression_report.json").resolve()
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[{'PASS' if failures == 0 else 'FAIL'}] stability.failures")
    print(f"[{'PASS' if sn_consistent else 'FAIL'}] stability.sn_consistent")
    print(f"[{'PASS' if mem_delta_kb <= mem_delta_kb_max else 'FAIL'}] stability.mem_delta")
    print(f"report={report_path}")
    print(f"RESULT: {'PASSED' if ok else 'FAILED'}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
