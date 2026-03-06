from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dsl_runtime.protocol_package import run_protocol_vectors


def main() -> int:
    parser = argparse.ArgumentParser(description="Run protocol package vectors.yaml cases.")
    parser.add_argument("--root", default="protocols", help="Protocol packages root directory")
    parser.add_argument("--protocol", required=True, help="Protocol package id")
    parser.add_argument("--json", action="store_true", help="Print full JSON result")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    result = run_protocol_vectors(root, args.protocol)
    total = len(result.cases)
    passed = sum(1 for c in result.cases if c.ok)
    print(f"[vectors] protocol={result.protocol_id} package={result.package_dir}")
    print(f"[vectors] passed={passed}/{total}")
    for case in result.cases:
        status = "PASS" if case.ok else "FAIL"
        print(f"- {status} {case.case_id} ({case.kind})")
    if args.json:
        payload = {
            "ok": result.ok,
            "protocol_id": result.protocol_id,
            "package_dir": result.package_dir,
            "cases": [
                {
                    "id": c.case_id,
                    "kind": c.kind,
                    "ok": c.ok,
                    "expected": c.expected,
                    "actual": c.actual,
                    "error": c.error,
                }
                for c in result.cases
            ],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if result.ok else 2


if __name__ == "__main__":
    sys.exit(main())
