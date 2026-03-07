from __future__ import annotations

from pathlib import Path
import shutil
import sys
import tempfile

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dsl_runtime.engine.context import RuntimeContext
from dsl_runtime.engine.v01_artifacts import export_v01_artifacts
from dsl_runtime.engine.v01_executor import execute_v01
from dsl_runtime.lang.ast_nodes import ArtifactsConfig, DefaultsConfig, RetryPolicy, ScriptAST, SessionConfig


class FakeChannel:
    def __init__(self, reads: list[bytes] | None = None) -> None:
        self.reads = list(reads or [])
        self.writes: list[bytes] = []

    def write(self, data):
        if isinstance(data, str):
            data = data.encode("utf-8")
        self.writes.append(bytes(data))

    def read(self, size: int = 1, timeout: float = 1.0) -> bytes:
        if not self.reads:
            return b""
        chunk = self.reads.pop(0)
        return chunk[:size]

    def read_event(self, timeout: float = 0.1):
        return None

    def close(self) -> None:
        return None


def _base_ast(steps: list[dict], artifacts_dir: str) -> ScriptAST:
    return ScriptAST(
        version="0.1",
        params={"sn": "SN001"},
        vars={"sn_read": ""},
        session=SessionConfig(
            transport="serial",
            port="COM5",
            baud=115200,
            data_bits=8,
            parity="none",
            stop_bits=1,
            encoding="ascii",
            eol="crlf",
            open_timeout_ms=3000,
            read_timeout_ms=50,
        ),
        defaults=DefaultsConfig(timeout_ms=200, retry=RetryPolicy(count=1, backoff_ms=10, strategy="fixed")),
        steps=steps,
        artifacts=ArtifactsConfig(dir=artifacts_dir, raw_log=True, summary_json=True, report_csv=False),
    )


def _run_ast(ast: ScriptAST, channel: FakeChannel):
    ctx = RuntimeContext({"default": channel}, "default", vars_init=dict(ast.vars), params_init=dict(ast.params))
    summary = execute_v01(ast, ctx)
    ctx.close()
    return summary, channel


def main() -> int:
    tmp_root = Path(tempfile.mkdtemp(prefix="protoflow_v01_reg_"))
    checks: list[tuple[str, bool]] = []
    try:
        # Case 1: send + expect + capture + assert success
        steps_ok = [
            {"id": "send_sn", "name": "send", "text": "AT+SETSN=${sn}"},
            {"id": "expect_ok", "name": "expect", "match": {"type": "contains", "pattern": "SN:SN001"}, "timeout_ms": 500},
            {"id": "capture_sn", "name": "capture", "regex": r"SN:([A-Z0-9]+)", "group": 1, "var": "sn_read"},
            {"id": "assert_sn", "name": "assert", "expr": "${sn_read} == ${sn}"},
        ]
        ast_ok = _base_ast(steps_ok, str(tmp_root / "ok_${now}"))
        summary_ok, ch_ok = _run_ast(ast_ok, FakeChannel([b"SN:SN001\r\n"]))
        checks.append(("ok.summary_true", bool(summary_ok.get("ok"))))
        checks.append(("ok.send_payload", any(w.endswith(b"\r\n") for w in ch_ok.writes)))
        checks.append(("ok.capture_var", summary_ok.get("vars", {}).get("sn_read") == "SN001"))

        out_dir_ok = export_v01_artifacts(ast_ok, summary_ok)
        checks.append(("ok.artifact_dir", bool(out_dir_ok and Path(out_dir_ok).exists())))
        checks.append(("ok.summary_json", bool(out_dir_ok and (Path(out_dir_ok) / "summary.json").exists())))
        checks.append(("ok.raw_log", bool(out_dir_ok and (Path(out_dir_ok) / "raw_log.jsonl").exists())))

        # Case 2: failure path + on_fail recovery step should run
        steps_fail = [
            {"id": "wait_ready", "name": "expect", "match": {"type": "contains", "pattern": "READY"}, "timeout_ms": 120, "retry": {"count": 1, "backoff_ms": 10, "strategy": "fixed"}, "on_fail": [{"name": "send", "text": "AT+RST"}]},
        ]
        ast_fail = _base_ast(steps_fail, str(tmp_root / "fail_${now}"))
        summary_fail, ch_fail = _run_ast(ast_fail, FakeChannel([]))
        checks.append(("fail.summary_false", not bool(summary_fail.get("ok"))))
        checks.append(("fail.on_fail_send", any(b"AT+RST" in w for w in ch_fail.writes)))

        out_dir_fail = export_v01_artifacts(ast_fail, summary_fail)
        checks.append(("fail.summary_json", bool(out_dir_fail and (Path(out_dir_fail) / "summary.json").exists())))

        # Case 3: controlled if/else flow (v0.2)
        steps_if = [
            {
                "id": "branch",
                "name": "if",
                "when": "${mode} == 'boot'",
                "then": [{"name": "send", "text": "BOOT"}],
                "else": [{"name": "send", "text": "APP"}],
            }
        ]
        ast_if = _base_ast(steps_if, str(tmp_root / "if_${now}"))
        ast_if.version = "0.2"
        ast_if.params["mode"] = "boot"
        summary_if, ch_if = _run_ast(ast_if, FakeChannel([]))
        checks.append(("if.summary_true", bool(summary_if.get("ok"))))
        checks.append(("if.then_branch", any(b"BOOT" in w for w in ch_if.writes)))
        checks.append(("if.else_not_sent", all(b"APP" not in w for w in ch_if.writes)))

        # Case 4: controlled loop flow (times + until)
        steps_loop = [
            {
                "id": "loop_send",
                "name": "loop",
                "times": 5,
                "until": "${last_loop_round} >= 2",
                "steps": [{"name": "send", "text": "AT"}],
            }
        ]
        ast_loop = _base_ast(steps_loop, str(tmp_root / "loop_${now}"))
        ast_loop.version = "0.2"
        ast_loop.vars["last_loop_round"] = 0
        summary_loop, ch_loop = _run_ast(ast_loop, FakeChannel([]))
        checks.append(("loop.summary_true", bool(summary_loop.get("ok"))))
        checks.append(("loop.iterations", len(ch_loop.writes) == 2))

        # Case 5: parse step (json/kv/csv)
        steps_parse = [
            {"id": "j", "name": "parse", "format": "json", "source": '{"a":1,"b":"x"}', "save_as": "pj"},
            {"id": "k", "name": "parse", "format": "kv", "source": "k1=v1;k2=v2", "save_as": "pk"},
            {"id": "c", "name": "parse", "format": "csv", "source": "x,y\n1,2\n", "save_as": "pc"},
            {"id": "p", "name": "path", "source": "${pj}", "path": "a", "save_as": "pa"},
            {"id": "m", "name": "measure", "metric": "voltage", "value": "12.1", "unit": "V"},
            {"id": "aj", "name": "assert", "expr": "${pj}['a'] == 1"},
            {"id": "ak", "name": "assert", "expr": "${pk}['k2'] == 'v2'"},
            {"id": "ac", "name": "assert", "expr": "${pc}['x'] == '1'"},
            {"id": "ap", "name": "assert", "expr": "${pa} == 1"},
            {"id": "am", "name": "assert", "expr": "${measure.voltage} == '12.1'"},
            {"id": "ar", "name": "assert_range", "value": "${measure.voltage}", "min": 12.0, "max": 12.2},
        ]
        ast_parse = _base_ast(steps_parse, str(tmp_root / "parse_${now}"))
        ast_parse.version = "0.2"
        summary_parse, _ = _run_ast(ast_parse, FakeChannel([]))
        checks.append(("parse.summary_true", bool(summary_parse.get("ok"))))

        # Case 6: controlled exec (allowlist + output capture)
        steps_exec = [
            {
                "id": "exec_echo",
                "name": "exec",
                "command": "python --version",
                "timeout_ms": 3000,
                "save_stdout_as": "exec_out",
            },
            {
                "id": "assert_exec",
                "name": "assert",
                "expr": "${last_exec_code} == 0",
            },
        ]
        ast_exec = _base_ast(steps_exec, str(tmp_root / "exec_${now}"))
        ast_exec.version = "0.2"
        ast_exec.security = {
            "exec": {
                "enabled": True,
                "allow_commands": ["python"],
                "cwd_allowlist": [str(ROOT_DIR)],
            }
        }
        summary_exec, _ = _run_ast(ast_exec, FakeChannel([]))
        checks.append(("exec.summary_true", bool(summary_exec.get("ok"))))

        # Case 7: controlled file operations
        file_path = str(tmp_root / "file_case" / "out.txt")
        steps_file = [
            {"id": "fw", "name": "file", "op": "write_text", "path": file_path, "content": "ABC"},
            {"id": "fa", "name": "file", "op": "append_text", "path": file_path, "content": "123"},
            {"id": "fe", "name": "file", "op": "exists", "path": file_path, "save_as": "f_exists"},
            {"id": "fr", "name": "file", "op": "read_text", "path": file_path, "save_as": "f_text"},
            {"id": "af1", "name": "assert", "expr": "${f_exists} == True"},
            {"id": "af2", "name": "assert", "expr": "${f_text} == 'ABC123'"},
        ]
        ast_file = _base_ast(steps_file, str(tmp_root / "file_${now}"))
        ast_file.version = "0.2"
        ast_file.security = {"file": {"root_allowlist": [str(tmp_root)]}}
        summary_file, _ = _run_ast(ast_file, FakeChannel([]))
        checks.append(("file.summary_true", bool(summary_file.get("ok"))))

        # Case 8: switch_session dry-run (no real serial reopen)
        steps_switch = [
            {"id": "sw", "name": "switch_session", "port": "COM9", "baud": 57600, "dry_run": True},
            {"id": "asw1", "name": "assert", "expr": "${last_session.port} == 'COM9'"},
            {"id": "asw2", "name": "assert", "expr": "${last_session.baud} == 57600"},
        ]
        ast_switch = _base_ast(steps_switch, str(tmp_root / "switch_${now}"))
        ast_switch.version = "0.2"
        summary_switch, _ = _run_ast(ast_switch, FakeChannel([]))
        checks.append(("switch.summary_true", bool(summary_switch.get("ok"))))

    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)

    ok = True
    for name, passed in checks:
        print(f"[{'PASS' if passed else 'FAIL'}] {name}")
        ok = ok and passed
    print(f"RESULT: {'PASSED' if ok else 'FAILED'}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
