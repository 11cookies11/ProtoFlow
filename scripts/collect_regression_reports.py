from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict, List


def _load_json(path: Path) -> Dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    return data


def _normalize_case_from_legacy(report: Dict[str, Any], source: Path) -> List[Dict[str, Any]]:
    if isinstance(report.get("cases"), list):
        out: List[Dict[str, Any]] = []
        for idx, item in enumerate(report["cases"]):
            if isinstance(item, dict):
                cid = str(item.get("id") or item.get("name") or f"case_{idx + 1}")
                out.append(
                    {
                        "id": cid,
                        "ok": bool(item.get("ok", False)),
                        "elapsed_ms": int(item.get("elapsed_ms", 0)),
                        "source": str(source),
                    }
                )
            elif isinstance(item, str):
                out.append({"id": item, "ok": True, "elapsed_ms": 0, "source": str(source)})
        return out
    return [
        {
            "id": source.stem,
            "ok": bool(report.get("ok", False)),
            "elapsed_ms": int(report.get("elapsed_ms", 0)),
            "source": str(source),
        }
    ]


def collect(input_dir: Path) -> Dict[str, Any]:
    files = sorted(input_dir.rglob("*report*.json"))
    merged_cases: List[Dict[str, Any]] = []
    for fp in files:
        data = _load_json(fp)
        if data is None:
            continue
        merged_cases.extend(_normalize_case_from_legacy(data, fp))
    overall_ok = all(bool(c.get("ok", False)) for c in merged_cases) if merged_cases else False
    return {
        "suite": "regression.aggregate",
        "ok": overall_ok,
        "generated_at": time.time(),
        "cases": merged_cases,
        "inputs": [str(x) for x in files],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect regression report json files into one result model.")
    parser.add_argument("--input-dir", default="runs", help="Directory to scan report json files")
    parser.add_argument("--output", default="runs/regression_aggregate_report.json", help="Output json path")
    args = parser.parse_args()

    inp = Path(args.input_dir).resolve()
    out = Path(args.output).resolve()
    result = collect(inp)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"aggregate report: {out}")
    print(f"cases={len(result['cases'])} ok={result['ok']}")
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
