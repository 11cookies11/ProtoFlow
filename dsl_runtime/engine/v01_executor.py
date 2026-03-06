from __future__ import annotations

import re
import time
import json
import csv
import io
import os
import shlex
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from dsl_runtime.lang.ast_nodes import ScriptAST
from dsl_runtime.lang.expression import eval_expr
from dsl_runtime.engine.channels import build_channels
from dsl_runtime.engine.context import RuntimeContext
from dsl_runtime.protocol_package import ProtocolPackageGateway, load_protocol_packages
from dsl_runtime.protocol_package.runtime import ProtocolCallContext


_EOL_MAP = {
    "none": b"",
    "cr": b"\r",
    "lf": b"\n",
    "crlf": b"\r\n",
}

_TPL_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_\.]*)\}")


def _render_template(value: str, env: Dict[str, Any]) -> str:
    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        if key in env:
            return str(env.get(key, ""))
        if "." in key:
            try:
                return str(_lookup_path(env, key))
            except Exception:
                return ""
        return str(env.get(key, ""))

    return _TPL_RE.sub(repl, value)


def _build_env(ctx: RuntimeContext, ast: ScriptAST) -> Dict[str, Any]:
    env: Dict[str, Any] = {}
    env.update(ctx.vars_snapshot())
    return env


def _render_object(value: Any, env: Dict[str, Any]) -> Any:
    if isinstance(value, str):
        return _render_template(value, env)
    if isinstance(value, list):
        return [_render_object(item, env) for item in value]
    if isinstance(value, dict):
        return {str(k): _render_object(v, env) for k, v in value.items()}
    return value


def _resolve_protocol_packages_dir(step: Dict[str, Any], ast: ScriptAST, ctx: RuntimeContext) -> Path:
    env = _build_env(ctx, ast)
    script_base = Path(ctx.script_path).resolve().parent if ctx.script_path else Path.cwd()
    explicit = step.get("packages_dir")
    if explicit is not None and str(explicit).strip():
        raw = _render_template(str(explicit), env)
        p = Path(raw)
        return p if p.is_absolute() else (script_base / p).resolve()
    env_dir = os.getenv("PROTOFLOW_PROTOCOLS_DIR")
    if env_dir:
        p = Path(env_dir)
        return p if p.is_absolute() else (script_base / p).resolve()
    return (script_base / "protocols").resolve()


def _get_protocol_gateway(step: Dict[str, Any], ast: ScriptAST, ctx: RuntimeContext) -> ProtocolPackageGateway:
    root = _resolve_protocol_packages_dir(step, ast, ctx)
    cache = getattr(ctx, "_protocol_gateway_cache", {})
    key = str(root)
    gateway = cache.get(key)
    if gateway is not None:
        return gateway
    load_result = load_protocol_packages(root)
    gateway = ProtocolPackageGateway(load_result.packages)
    cache[key] = gateway
    setattr(ctx, "_protocol_gateway_cache", cache)
    if load_result.issues:
        ctx.logger.warning(f"[protocol] load issues at {root}: {len(load_result.issues)}")
    return gateway


def _text_to_bytes(text: str, *, encoding: str, eol: str) -> bytes:
    tail = _EOL_MAP.get(eol, b"")
    if encoding == "hex":
        payload = bytes.fromhex(text.replace(" ", ""))
        return payload + tail
    codec = "utf-8" if encoding == "utf8" else "ascii"
    return text.encode(codec) + tail


def _run_send_step(step: Dict[str, Any], ast: ScriptAST, ctx: RuntimeContext) -> None:
    session = ast.session
    if session is None:
        raise ValueError("session is required for v0.1")

    env = _build_env(ctx, ast)
    encoding = str(step.get("encoding") or session.encoding).lower()
    eol = str(step.get("eol") or session.eol).lower()

    if "hex" in step and step.get("hex") is not None:
        raw_hex = _render_template(str(step.get("hex")), env)
        payload = bytes.fromhex(raw_hex.replace(" ", ""))
    else:
        if "text" not in step:
            raise ValueError("send step requires text or hex")
        text = _render_template(str(step.get("text", "")), env)
        payload = _text_to_bytes(text, encoding=encoding, eol=eol)

    ctx.channel_write(payload)
    ctx.set_var("last_tx_hex", payload.hex().upper())


def _match_text(match_cfg: Dict[str, Any], text: str) -> bool:
    match_type = str(match_cfg.get("type", "contains")).strip().lower()
    pattern = str(match_cfg.get("pattern", ""))
    if not pattern:
        raise ValueError("expect.match.pattern is required")
    if match_type == "contains":
        return pattern in text
    if match_type == "startswith":
        return text.startswith(pattern)
    if match_type == "regex":
        raw_flags = str(match_cfg.get("flags", ""))
        flags = 0
        if "i" in raw_flags:
            flags |= re.IGNORECASE
        if "m" in raw_flags:
            flags |= re.MULTILINE
        if "s" in raw_flags:
            flags |= re.DOTALL
        return re.search(pattern, text, flags=flags) is not None
    raise ValueError("expect.match.type must be contains/regex/startswith")


def _decode_rx(chunk: bytes, *, encoding: str) -> str:
    if encoding == "hex":
        return chunk.hex().upper()
    codec = "utf-8" if encoding == "utf8" else "ascii"
    return chunk.decode(codec, errors="ignore")


def _run_expect_step(step: Dict[str, Any], ast: ScriptAST, ctx: RuntimeContext) -> None:
    session = ast.session
    if session is None:
        raise ValueError("session is required for v0.1")

    match_cfg = step.get("match")
    if not isinstance(match_cfg, dict):
        raise ValueError("expect.match is required")

    timeout_ms = int(step.get("timeout_ms", ast.defaults.timeout_ms))
    if timeout_ms <= 0:
        raise ValueError("expect.timeout_ms must be > 0")

    encoding = str(step.get("encoding") or session.encoding).lower()
    per_read_timeout = max(0.01, session.read_timeout_ms / 1000.0)
    deadline = time.time() + (timeout_ms / 1000.0)
    rx_buf = bytearray()
    while time.time() < deadline:
        remaining = max(0.01, deadline - time.time())
        chunk = ctx.channel.read(256, timeout=min(per_read_timeout, remaining))
        if not chunk:
            continue
        rx_buf.extend(chunk)
        text = _decode_rx(bytes(rx_buf), encoding=encoding)
        if _match_text(match_cfg, text):
            ctx.set_var("last_rx_text", text)
            ctx.set_var("last_rx_hex", bytes(rx_buf).hex().upper())
            captures = step.get("capture")
            if captures:
                _apply_capture_rules(text, captures, ast, ctx)
            return

    raise TimeoutError("expect timeout: match not found")


def _apply_capture_rules(text: str, captures: Any, ast: ScriptAST, ctx: RuntimeContext) -> None:
    if isinstance(captures, dict):
        items = [captures]
    elif isinstance(captures, list):
        items = captures
    else:
        raise ValueError("capture must be a mapping or list")

    env = _build_env(ctx, ast)
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"capture[{idx}] must be a mapping")
        var_name = str(item.get("var", "")).strip()
        regex = item.get("regex")
        if not var_name or not regex:
            raise ValueError(f"capture[{idx}] requires var and regex")
        pattern = _render_template(str(regex), env)
        group = int(item.get("group", 1))
        match = re.search(pattern, text)
        if match is None:
            raise ValueError(f"capture[{idx}] regex not matched")
        try:
            value = match.group(group)
        except IndexError as exc:
            raise ValueError(f"capture[{idx}] group index out of range: {group}") from exc
        ctx.set_var(var_name, value)
        ctx.set_var("last_capture_var", var_name)
        ctx.set_var("last_capture_value", value)
        env[var_name] = value


def _run_capture_step(step: Dict[str, Any], ast: ScriptAST, ctx: RuntimeContext) -> None:
    env = _build_env(ctx, ast)
    source_raw = step.get("source", "${last_rx_text}")
    source_text = _render_template(str(source_raw), env)
    if not source_text:
        raise ValueError("capture source is empty")
    _apply_capture_rules(source_text, step, ast, ctx)


def _parse_kv_text(text: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    lines = text.replace(";", "\n").splitlines()
    for raw in lines:
        line = raw.strip()
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def _parse_csv_text(text: str) -> Any:
    f = io.StringIO(text.strip())
    reader = csv.DictReader(f)
    rows = [dict(row) for row in reader]
    if len(rows) == 1:
        return rows[0]
    return rows


def _run_parse_step(step: Dict[str, Any], ast: ScriptAST, ctx: RuntimeContext) -> None:
    env = _build_env(ctx, ast)
    fmt = str(step.get("format", "")).strip().lower()
    if fmt not in {"json", "kv", "csv"}:
        raise ValueError("parse.format must be json/kv/csv")
    source_raw = step.get("source", "${last_rx_text}")
    source_text = _render_template(str(source_raw), env)
    save_as = str(step.get("save_as", "parsed")).strip() or "parsed"

    if fmt == "json":
        parsed = json.loads(source_text)
    elif fmt == "kv":
        parsed = _parse_kv_text(source_text)
    else:
        parsed = _parse_csv_text(source_text)

    ctx.set_var(save_as, parsed)
    ctx.set_var("last_parsed", parsed)


def _lookup_path(obj: Any, path: str) -> Any:
    current = obj
    for token in path.split("."):
        key = token.strip()
        if not key:
            continue
        if isinstance(current, dict):
            if key not in current:
                raise KeyError(f"path segment not found: {key}")
            current = current[key]
            continue
        if isinstance(current, list):
            idx = int(key)
            current = current[idx]
            continue
        raise KeyError(f"path segment not accessible on type: {type(current).__name__}")
    return current


def _run_path_step(step: Dict[str, Any], ast: ScriptAST, ctx: RuntimeContext) -> None:
    env = _build_env(ctx, ast)
    source_raw = step.get("source", "${last_parsed}")
    source_text = _render_template(str(source_raw), env)
    source_obj: Any = source_text
    # Prefer direct object when source points to a runtime variable name.
    if isinstance(source_raw, str) and source_raw.startswith("${") and source_raw.endswith("}"):
        key = source_raw[2:-1].strip()
        vars_map = ctx.vars_snapshot()
        if key in vars_map:
            source_obj = vars_map[key]
    path = str(step.get("path", "")).strip()
    if not path:
        raise ValueError("path.path is required")
    save_as = str(step.get("save_as", "")).strip()
    if not save_as:
        raise ValueError("path.save_as is required")
    value = _lookup_path(source_obj, path)
    ctx.set_var(save_as, value)
    ctx.set_var("last_path_value", value)


def _run_measure_step(step: Dict[str, Any], ast: ScriptAST, ctx: RuntimeContext) -> None:
    env = _build_env(ctx, ast)
    metric = str(step.get("metric", "")).strip()
    if not metric:
        raise ValueError("measure.metric is required")
    raw_value = step.get("value")
    if raw_value is None:
        raise ValueError("measure.value is required")
    value_text = _render_template(str(raw_value), env)
    unit = str(step.get("unit", "")).strip()
    item = {"metric": metric, "value": value_text, "unit": unit, "ts": time.time()}
    metrics = ctx.vars.get("metrics")
    if not isinstance(metrics, list):
        metrics = []
    metrics.append(item)
    ctx.set_var("metrics", metrics)
    ctx.set_var(f"measure.{metric}", value_text)
    ctx.set_var("last_measure", item)


def _to_float(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    return float(str(value).strip())


def _run_assert_range_step(step: Dict[str, Any], ast: ScriptAST, ctx: RuntimeContext) -> None:
    env = _build_env(ctx, ast)
    raw_value = step.get("value")
    if raw_value is None:
        raise ValueError("assert_range.value is required")
    value = _to_float(_render_template(str(raw_value), env))
    message = str(step.get("message", "range assert failed"))

    checks = 0
    min_v = step.get("min")
    if min_v is not None:
        checks += 1
        if value < _to_float(_render_template(str(min_v), env)):
            raise AssertionError(message)

    max_v = step.get("max")
    if max_v is not None:
        checks += 1
        if value > _to_float(_render_template(str(max_v), env)):
            raise AssertionError(message)

    abs_err = step.get("abs_err")
    target = step.get("target")
    if abs_err is not None:
        if target is None:
            raise ValueError("assert_range.target is required when abs_err is set")
        checks += 1
        delta = abs(value - _to_float(_render_template(str(target), env)))
        if delta > _to_float(_render_template(str(abs_err), env)):
            raise AssertionError(message)

    in_set = step.get("in_set")
    if in_set is not None:
        if not isinstance(in_set, list) or not in_set:
            raise ValueError("assert_range.in_set must be a non-empty list")
        checks += 1
        candidates = [_to_float(_render_template(str(item), env)) for item in in_set]
        if value not in candidates:
            raise AssertionError(message)

    if checks == 0:
        raise ValueError("assert_range requires at least one rule: min/max/abs_err/in_set")


def _run_exec_step(step: Dict[str, Any], ast: ScriptAST, ctx: RuntimeContext) -> None:
    env = _build_env(ctx, ast)
    command_raw = step.get("command")
    if command_raw is None:
        raise ValueError("exec.command is required")
    command = _render_template(str(command_raw), env).strip()
    if not command:
        raise ValueError("exec.command is empty")

    sec_cfg = ast.security.get("exec") if isinstance(ast.security, dict) else None
    if not isinstance(sec_cfg, dict) or not bool(sec_cfg.get("enabled", False)):
        raise PermissionError("EXEC_NOT_ALLOWED: security.exec.enabled is false")

    allow_commands = sec_cfg.get("allow_commands") or []
    if not isinstance(allow_commands, list) or not allow_commands:
        raise PermissionError("EXEC_NOT_ALLOWED: security.exec.allow_commands is empty")
    allow_set = {str(x).lower() for x in allow_commands}

    argv = shlex.split(command, posix=False)
    if not argv:
        raise ValueError("exec.command parse failed")
    cmd_name = Path(argv[0]).name.lower()
    if cmd_name not in allow_set:
        raise PermissionError(f"EXEC_NOT_ALLOWED: command not in allowlist: {cmd_name}")

    cwd = _render_template(str(step.get("cwd", os.getcwd())), env)
    allow_dirs = sec_cfg.get("cwd_allowlist") or []
    if not isinstance(allow_dirs, list):
        raise PermissionError("EXEC_NOT_ALLOWED: security.exec.cwd_allowlist invalid")
    cwd_resolved = str(Path(cwd).resolve())
    if allow_dirs:
        allowed = False
        for raw in allow_dirs:
            p = str(Path(_render_template(str(raw), env)).resolve())
            if cwd_resolved.startswith(p):
                allowed = True
                break
        if not allowed:
            raise PermissionError("EXEC_NOT_ALLOWED: cwd not in allowlist")

    timeout_ms = int(step.get("timeout_ms", ast.defaults.timeout_ms))
    proc = subprocess.run(
        argv,
        cwd=cwd_resolved,
        capture_output=True,
        text=True,
        timeout=max(1, timeout_ms) / 1000.0,
        shell=False,
    )

    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    ctx.set_var("last_exec", {"command": command, "returncode": proc.returncode, "stdout": stdout, "stderr": stderr})
    ctx.set_var("last_exec_code", proc.returncode)
    if step.get("save_stdout_as"):
        ctx.set_var(str(step.get("save_stdout_as")), stdout)
    if step.get("save_stderr_as"):
        ctx.set_var(str(step.get("save_stderr_as")), stderr)
    if proc.returncode != 0:
        raise RuntimeError(f"EXEC_FAILED: returncode={proc.returncode}")


def _is_path_allowed(path: Path, allow_roots: List[str], env: Dict[str, Any]) -> bool:
    if not allow_roots:
        return False
    target = str(path.resolve())
    for raw in allow_roots:
        root = str(Path(_render_template(str(raw), env)).resolve())
        if target.startswith(root):
            return True
    return False


def _run_file_step(step: Dict[str, Any], ast: ScriptAST, ctx: RuntimeContext) -> None:
    env = _build_env(ctx, ast)
    op = str(step.get("op", "")).strip().lower()
    if op not in {"read_text", "write_text", "append_text", "exists"}:
        raise ValueError("file.op must be read_text/write_text/append_text/exists")
    raw_path = step.get("path")
    if raw_path is None:
        raise ValueError("file.path is required")
    path = Path(_render_template(str(raw_path), env)).resolve()

    sec_cfg = ast.security.get("file") if isinstance(ast.security, dict) else None
    allow_roots = []
    if isinstance(sec_cfg, dict):
        allow_roots = sec_cfg.get("root_allowlist") or []
    if not isinstance(allow_roots, list):
        raise PermissionError("FILE_NOT_ALLOWED: security.file.root_allowlist invalid")
    if not _is_path_allowed(path, allow_roots, env):
        raise PermissionError("FILE_NOT_ALLOWED: path not in allowlist")

    if op == "write_text":
        content = _render_template(str(step.get("content", "")), env)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        ctx.set_var("last_file", {"op": op, "path": str(path), "bytes": len(content.encode("utf-8"))})
        return

    if op == "append_text":
        content = _render_template(str(step.get("content", "")), env)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(content)
        ctx.set_var("last_file", {"op": op, "path": str(path), "bytes": len(content.encode("utf-8"))})
        return

    if op == "exists":
        save_as = str(step.get("save_as", "file_exists")).strip() or "file_exists"
        ok = path.exists()
        ctx.set_var(save_as, ok)
        ctx.set_var("last_file", {"op": op, "path": str(path), "exists": ok})
        return

    # read_text
    text = path.read_text(encoding="utf-8")
    save_as = str(step.get("save_as", "file_text")).strip() or "file_text"
    ctx.set_var(save_as, text)
    ctx.set_var("last_file", {"op": op, "path": str(path), "bytes": len(text.encode("utf-8"))})


def _run_switch_session_step(step: Dict[str, Any], ast: ScriptAST, ctx: RuntimeContext) -> None:
    session = ast.session
    if session is None:
        raise ValueError("session is required")
    env = _build_env(ctx, ast)

    next_port = _render_template(str(step.get("port", session.port)), env).strip()
    next_baud = int(_render_template(str(step.get("baud", session.baud)), env))
    next_data_bits = int(_render_template(str(step.get("data_bits", session.data_bits)), env))
    next_parity = _render_template(str(step.get("parity", session.parity)), env).strip().lower()
    next_stop_bits = int(_render_template(str(step.get("stop_bits", session.stop_bits)), env))
    next_encoding = _render_template(str(step.get("encoding", session.encoding)), env).strip().lower()
    next_eol = _render_template(str(step.get("eol", session.eol)), env).strip().lower()
    dry_run = bool(step.get("dry_run", False))

    if not dry_run:
        channels = build_channels({"default": {"type": "serial", "device": next_port, "baudrate": next_baud}})
        old = ctx.channel
        ctx.channel = channels["default"]
        ctx.channels["default"] = channels["default"]
        if hasattr(old, "close"):
            try:
                old.close()  # type: ignore[attr-defined]
            except Exception:
                pass

    session.port = next_port
    session.baud = next_baud
    session.data_bits = next_data_bits
    session.parity = next_parity
    session.stop_bits = next_stop_bits
    session.encoding = next_encoding
    session.eol = next_eol
    ctx.set_var(
        "last_session",
        {
            "port": next_port,
            "baud": next_baud,
            "data_bits": next_data_bits,
            "parity": next_parity,
            "stop_bits": next_stop_bits,
            "encoding": next_encoding,
            "eol": next_eol,
            "dry_run": dry_run,
        },
    )


def _resolve_protocol_method(step_name: str, step: Dict[str, Any]) -> str:
    explicit = str(step.get("method", "")).strip().lower()
    if explicit:
        return explicit
    if "." in step_name:
        return step_name.split(".", 1)[1].strip().lower()
    raise ValueError("protocol step requires method")


def _run_protocol_step(step_name: str, step: Dict[str, Any], ast: ScriptAST, ctx: RuntimeContext) -> None:
    method = _resolve_protocol_method(step_name, step)
    if method not in {"send", "recv", "rpc"}:
        raise ValueError("protocol method must be send/recv/rpc")

    protocol_id = str(step.get("protocol", "")).strip()
    if not protocol_id:
        raise ValueError("protocol step requires protocol id")

    if method == "recv":
        raw_payload = step.get("expect", step.get("payload", {}))
    else:
        raw_payload = step.get("request", step.get("payload", {}))
    if raw_payload is None:
        raw_payload = {}
    if not isinstance(raw_payload, dict):
        raise ValueError("protocol payload must be a mapping")

    env = _build_env(ctx, ast)
    payload = _render_object(raw_payload, env)
    timeout_ms = int(step.get("timeout_ms", ast.defaults.timeout_ms))
    if timeout_ms <= 0:
        raise ValueError("protocol.timeout_ms must be > 0")

    gateway = _get_protocol_gateway(step, ast, ctx)
    call_ctx = ProtocolCallContext(
        channel=ctx.channel,
        logger=ctx.logger,
        vars=ctx.vars_snapshot(),
        timeout_ms=timeout_ms,
        artifacts={},
    )
    result = gateway.call(protocol_id=protocol_id, method=method, ctx=call_ctx, payload=payload)
    if not result.ok:
        error = result.error or {}
        code = error.get("code", "PROTOCOL_CALL_FAILED")
        message = error.get("message", "protocol call failed")
        raise RuntimeError(f"{code}: {message}")

    save_as = str(step.get("save_as", "last_protocol_result")).strip() or "last_protocol_result"
    ctx.set_var(save_as, result.data)
    ctx.set_var(
        "last_protocol_call",
        {
            "protocol": protocol_id,
            "method": method,
            "timeout_ms": timeout_ms,
            "result": result.data,
        },
    )


def _run_sleep_step(step: Dict[str, Any]) -> None:
    ms = int(step.get("ms", 0))
    if ms < 0:
        raise ValueError("sleep.ms must be >= 0")
    if ms == 0:
        return
    time.sleep(ms / 1000.0)


def _eval_assert_expr(expr: str, env: Dict[str, Any]) -> bool:
    # Reuse existing expression engine by mapping ${var} -> $var.
    normalized = re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_\.]*)\}", r"$\1", expr)
    return bool(eval_expr(normalized, env))


def _assert_clause(clause: Dict[str, Any], ast: ScriptAST, ctx: RuntimeContext) -> bool:
    if not isinstance(clause, dict):
        raise ValueError("assert clause must be a mapping")
    env = _build_env(ctx, ast)
    if "expr" in clause:
        return _eval_assert_expr(str(clause.get("expr", "")), env)
    if "match" in clause:
        match_cfg = clause.get("match")
        if not isinstance(match_cfg, dict):
            raise ValueError("assert.match must be a mapping")
        source_raw = clause.get("source", "${last_rx_text}")
        source_text = _render_template(str(source_raw), env)
        return _match_text(match_cfg, source_text)
    raise ValueError("assert clause requires expr or match")


def _run_assert_step(step: Dict[str, Any], ast: ScriptAST, ctx: RuntimeContext) -> None:
    message = str(step.get("message", "assert failed"))
    if "all" in step:
        all_items = step.get("all")
        if not isinstance(all_items, list) or not all_items:
            raise ValueError("assert.all must be a non-empty list")
        result = all(_assert_clause(item, ast, ctx) for item in all_items)
    elif "any" in step:
        any_items = step.get("any")
        if not isinstance(any_items, list) or not any_items:
            raise ValueError("assert.any must be a non-empty list")
        result = any(_assert_clause(item, ast, ctx) for item in any_items)
    else:
        result = _assert_clause(step, ast, ctx)
    if not result:
        raise AssertionError(message)


def _run_if_step(step: Dict[str, Any], ast: ScriptAST, ctx: RuntimeContext) -> None:
    when_expr = str(step.get("when", "")).strip()
    if not when_expr:
        raise ValueError("if.when is required")
    env = _build_env(ctx, ast)
    cond = _eval_assert_expr(when_expr, env)
    branch_key = "then" if cond else "else"
    branch_steps = step.get(branch_key, [])
    if branch_steps is None:
        branch_steps = []
    if not isinstance(branch_steps, list):
        raise ValueError(f"if.{branch_key} must be a list")
    for idx, child in enumerate(branch_steps):
        if not isinstance(child, dict):
            raise ValueError(f"if.{branch_key}[{idx}] must be a mapping")
        _run_step_with_reliability(child, ast, ctx)


def _run_loop_step(step: Dict[str, Any], ast: ScriptAST, ctx: RuntimeContext) -> None:
    body = step.get("steps")
    if not isinstance(body, list) or not body:
        raise ValueError("loop.steps must be a non-empty list")
    times = step.get("times")
    until = step.get("until")
    if times is None and not until:
        raise ValueError("loop requires times or until")
    max_rounds = int(times) if times is not None else 1000000
    if max_rounds < 0:
        raise ValueError("loop.times must be >= 0")

    rounds = 0
    while rounds < max_rounds:
        if until:
            env = _build_env(ctx, ast)
            if _eval_assert_expr(str(until), env):
                break
        for idx, child in enumerate(body):
            if not isinstance(child, dict):
                raise ValueError(f"loop.steps[{idx}] must be a mapping")
            _run_step_with_reliability(child, ast, ctx)
        rounds += 1
        ctx.set_var("last_loop_round", rounds)


def _resolve_retry(step: Dict[str, Any], ast: ScriptAST) -> Dict[str, int | str]:
    retry_cfg = step.get("retry")
    if retry_cfg is None:
        count = int(ast.defaults.retry.count)
        backoff_ms = int(ast.defaults.retry.backoff_ms)
        strategy = str(ast.defaults.retry.strategy)
        return {"count": count, "backoff_ms": backoff_ms, "strategy": strategy}
    if not isinstance(retry_cfg, dict):
        raise ValueError("step.retry must be a mapping")
    count = int(retry_cfg.get("count", ast.defaults.retry.count))
    backoff_ms = int(retry_cfg.get("backoff_ms", ast.defaults.retry.backoff_ms))
    strategy = str(retry_cfg.get("strategy", ast.defaults.retry.strategy))
    if count < 0:
        raise ValueError("step.retry.count must be >= 0")
    if backoff_ms < 0:
        raise ValueError("step.retry.backoff_ms must be >= 0")
    if strategy not in {"fixed", "exponential"}:
        raise ValueError("step.retry.strategy must be fixed or exponential")
    return {"count": count, "backoff_ms": backoff_ms, "strategy": strategy}


def _dispatch_step(step: Dict[str, Any], ast: ScriptAST, ctx: RuntimeContext) -> None:
    name = str(step.get("name", "")).strip().lower()
    if not name:
        raise ValueError("step.name is required")
    if name == "send":
        _run_send_step(step, ast, ctx)
        return
    if name == "expect":
        _run_expect_step(step, ast, ctx)
        return
    if name == "sleep":
        _run_sleep_step(step)
        return
    if name == "capture":
        _run_capture_step(step, ast, ctx)
        return
    if name == "parse":
        _run_parse_step(step, ast, ctx)
        return
    if name == "path":
        _run_path_step(step, ast, ctx)
        return
    if name == "measure":
        _run_measure_step(step, ast, ctx)
        return
    if name == "assert_range":
        _run_assert_range_step(step, ast, ctx)
        return
    if name == "exec":
        _run_exec_step(step, ast, ctx)
        return
    if name == "file":
        _run_file_step(step, ast, ctx)
        return
    if name == "switch_session":
        _run_switch_session_step(step, ast, ctx)
        return
    if name in {"protocol.send", "protocol.recv", "protocol.rpc", "protocol"}:
        _run_protocol_step(name, step, ast, ctx)
        return
    if name == "assert":
        _run_assert_step(step, ast, ctx)
        return
    if name == "if":
        _run_if_step(step, ast, ctx)
        return
    if name == "loop":
        _run_loop_step(step, ast, ctx)
        return
    raise NotImplementedError(f"v0.1 step not implemented yet: {name}")


def _run_on_fail(step: Dict[str, Any], ast: ScriptAST, ctx: RuntimeContext) -> int:
    hooks = step.get("on_fail")
    if hooks is None:
        return 0
    if not isinstance(hooks, list):
        raise ValueError("step.on_fail must be a list")
    ran = 0
    for idx, hook in enumerate(hooks):
        if not isinstance(hook, dict):
            raise ValueError(f"step.on_fail[{idx}] must be a mapping")
        try:
            _dispatch_step(hook, ast, ctx)
            ran += 1
        except Exception as exc:
            ctx.logger.warning(f"on_fail step ignored due to error: {exc}")
    return ran


def _run_step_with_reliability(step: Dict[str, Any], ast: ScriptAST, ctx: RuntimeContext) -> Dict[str, Any]:
    retry = _resolve_retry(step, ast)
    count = int(retry["count"])
    backoff_ms = int(retry["backoff_ms"])
    strategy = str(retry["strategy"])
    last_error: Exception | None = None
    attempts = 0

    for attempt in range(count + 1):
        attempts += 1
        try:
            _dispatch_step(step, ast, ctx)
            return {"attempts": attempts, "retry_count": count, "on_fail_steps": 0}
        except Exception as exc:
            last_error = exc
            if attempt >= count:
                break
            delay_ms = backoff_ms if strategy == "fixed" else backoff_ms * (2**attempt)
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)

    on_fail_steps = 0
    try:
        on_fail_steps = _run_on_fail(step, ast, ctx)
    finally:
        if last_error is not None:
            raise last_error
    return {"attempts": attempts, "retry_count": count, "on_fail_steps": on_fail_steps}


def _map_error_code(exc: Exception) -> str:
    msg = str(exc)
    if isinstance(exc, PermissionError):
        if "EXEC_NOT_ALLOWED" in msg:
            return "EXEC_NOT_ALLOWED"
        if "FILE_NOT_ALLOWED" in msg:
            return "FILE_NOT_ALLOWED"
        return "PERMISSION_DENIED"
    if isinstance(exc, TimeoutError):
        return "STEP_TIMEOUT"
    if isinstance(exc, AssertionError):
        return "ASSERT_FAILED"
    if isinstance(exc, NotImplementedError):
        return "STEP_NOT_IMPLEMENTED"
    if isinstance(exc, RuntimeError):
        if "EXEC_FAILED" in msg:
            return "EXEC_FAILED"
        if "PROTOCOL_" in msg:
            return "PROTOCOL_CALL_FAILED"
        return "RUNTIME_FAILED"
    if isinstance(exc, FileNotFoundError):
        return "FILE_FAILED"
    if isinstance(exc, ValueError):
        if "parse." in msg:
            return "PARSE_FAILED"
        if "capture" in msg:
            return "CAPTURE_FAILED"
        if "range" in msg:
            return "RANGE_ASSERT_FAILED"
        return "VALIDATION_FAILED"
    return "UNEXPECTED_EXCEPTION"


def _error_payload(exc: Exception, step_id: str) -> Dict[str, Any]:
    return {
        "code": _map_error_code(exc),
        "message": str(exc),
        "step_id": step_id,
        "ts": time.time(),
    }


def execute_v01(ast: ScriptAST, ctx: RuntimeContext) -> Dict[str, Any]:
    started_at = time.time()
    traces: List[Dict[str, Any]] = []
    error: Dict[str, Any] | None = None

    for idx, step in enumerate(ast.steps):
        step_id = str(step.get("id") or f"step_{idx + 1}")
        step_name = str(step.get("name") or "")
        t0 = time.time()
        trace: Dict[str, Any] = {
            "index": idx,
            "step_id": step_id,
            "name": step_name,
            "started_at": t0,
        }
        try:
            reliability = _run_step_with_reliability(step, ast, ctx)
            trace["status"] = "ok"
            trace.update(reliability)
        except Exception as exc:
            trace["status"] = "error"
            trace["error"] = _error_payload(exc, step_id)
            error = _error_payload(exc, step_id)
            traces.append(trace)
            break
        finally:
            trace["ended_at"] = time.time()
            trace["elapsed_ms"] = int((trace["ended_at"] - trace["started_at"]) * 1000)
            vars_snap = ctx.vars_snapshot()
            trace["last_tx_hex"] = vars_snap.get("last_tx_hex")
            trace["last_rx_text"] = vars_snap.get("last_rx_text")
            trace["last_rx_hex"] = vars_snap.get("last_rx_hex")
            if trace not in traces:
                traces.append(trace)

    ended_at = time.time()
    return {
        "ok": error is None,
        "error": error,
        "started_at": started_at,
        "ended_at": ended_at,
        "elapsed_ms": int((ended_at - started_at) * 1000),
        "steps": traces,
        "vars": ctx.vars_snapshot(),
    }
