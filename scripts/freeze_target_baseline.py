from __future__ import annotations

import argparse
import io
import json
import sys
import time
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.target_emulator_fault_regression import main as target_fault_main
from scripts.target_emulator_regression import main as target_main


def _run_case(name: str, fn: Callable[[], int]) -> Dict[str, object]:
    t0 = time.time()
    buf = io.StringIO()
    code = 2
    err = ""
    try:
        with redirect_stdout(buf):
            code = int(fn())
    except Exception as exc:
        err = str(exc)
    elapsed_ms = int((time.time() - t0) * 1000)
    out = buf.getvalue()
    return {
        "name": name,
        "ok": code == 0 and not err,
        "exit_code": code,
        "elapsed_ms": elapsed_ms,
        "error": err,
        "stdout": out,
    }


def _build_markdown(report: Dict[str, object]) -> str:
    lines: List[str] = []
    lines.append("# Target Emulator Baseline Report")
    lines.append("")
    lines.append(f"- baseline: {report['baseline']}")
    lines.append(f"- generated_at: {report['generated_at']}")
    lines.append(f"- overall_ok: {report['overall_ok']}")
    lines.append("")
    lines.append("## Cases")
    for case in report["cases"]:  # type: ignore[index]
        c = case  # type: ignore[assignment]
        lines.append(
            f"- {c['name']}: {'PASS' if c['ok'] else 'FAIL'} (exit={c['exit_code']}, elapsed_ms={c['elapsed_ms']})"
        )
    lines.append("")
    lines.append("## Notes")
    lines.append("- This is a frozen v0.1 target-emulator baseline snapshot.")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Freeze target emulator baseline report")
    parser.add_argument("--baseline", default="v0.1", help="baseline tag")
    parser.add_argument("--output-dir", default="docs/target-emulator-baseline/v0.1", help="report output directory")
    parser.add_argument("--stamp", default="", help="report stamp (default YYYYMMDD)")
    args = parser.parse_args()

    out_dir = (ROOT / args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    stamp = args.stamp.strip() or datetime.now().strftime("%Y%m%d")
    cases = [
        _run_case("target_emulator_regression", target_main),
        _run_case("target_emulator_fault_regression", target_fault_main),
    ]
    overall_ok = all(bool(item["ok"]) for item in cases)
    report = {
        "baseline": args.baseline,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "overall_ok": overall_ok,
        "cases": cases,
    }

    json_path = out_dir / f"baseline_report_{stamp}.json"
    md_path = out_dir / f"baseline_report_{stamp}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(_build_markdown(report), encoding="utf-8")

    latest_json = out_dir / "baseline_report_latest.json"
    latest_md = out_dir / "baseline_report_latest.md"
    latest_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    latest_md.write_text(_build_markdown(report), encoding="utf-8")

    print(f"baseline report written: {json_path}")
    print(f"baseline report written: {md_path}")
    return 0 if overall_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
