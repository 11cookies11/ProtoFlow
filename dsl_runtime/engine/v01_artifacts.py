from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict

from dsl_runtime.lang.ast_nodes import ScriptAST


_TPL_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def _render_template(value: str, env: Dict[str, Any]) -> str:
    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        return str(env.get(key, ""))

    return _TPL_RE.sub(repl, value)


def export_v01_artifacts(ast: ScriptAST, summary: Dict[str, Any]) -> str | None:
    if ast.artifacts is None:
        return None

    env: Dict[str, Any] = {"now": int(summary.get("started_at", 0))}
    vars_map = summary.get("vars")
    if isinstance(vars_map, dict):
        env.update(vars_map)

    raw_dir = ast.artifacts.dir or "./runs"
    out_dir = Path(_render_template(raw_dir, env))
    out_dir.mkdir(parents=True, exist_ok=True)

    if ast.artifacts.raw_log:
        raw_path = out_dir / "raw_log.jsonl"
        with raw_path.open("w", encoding="utf-8") as f:
            for item in summary.get("steps", []):
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

    if ast.artifacts.summary_json:
        summary_path = out_dir / "summary.json"
        with summary_path.open("w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

    if ast.artifacts.report_csv:
        csv_path = out_dir / "report.csv"
        with csv_path.open("w", encoding="utf-8") as f:
            f.write("index,step_id,name,status,elapsed_ms,error_code,error_message\n")
            for item in summary.get("steps", []):
                err = item.get("error") or {}
                row = [
                    item.get("index", ""),
                    item.get("step_id", ""),
                    item.get("name", ""),
                    item.get("status", ""),
                    item.get("elapsed_ms", ""),
                    err.get("code", ""),
                    str(err.get("message", "")).replace(",", " "),
                ]
                f.write(",".join(str(x) for x in row) + "\n")

    return str(out_dir)
