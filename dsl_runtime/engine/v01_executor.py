from __future__ import annotations

import re
import time
import json
import csv
import io
from typing import Any, Dict, List

from dsl_runtime.lang.ast_nodes import ScriptAST
from dsl_runtime.lang.expression import eval_expr
from dsl_runtime.engine.context import RuntimeContext


_EOL_MAP = {
    "none": b"",
    "cr": b"\r",
    "lf": b"\n",
    "crlf": b"\r\n",
}

_TPL_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def _render_template(value: str, env: Dict[str, Any]) -> str:
    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        return str(env.get(key, ""))

    return _TPL_RE.sub(repl, value)


def _build_env(ctx: RuntimeContext, ast: ScriptAST) -> Dict[str, Any]:
    env: Dict[str, Any] = {}
    env.update(ctx.vars_snapshot())
    return env


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


def _run_sleep_step(step: Dict[str, Any]) -> None:
    ms = int(step.get("ms", 0))
    if ms < 0:
        raise ValueError("sleep.ms must be >= 0")
    if ms == 0:
        return
    time.sleep(ms / 1000.0)


def _eval_assert_expr(expr: str, env: Dict[str, Any]) -> bool:
    # Reuse existing expression engine by mapping ${var} -> $var.
    normalized = re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", r"$\1", expr)
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


def _run_on_fail(step: Dict[str, Any], ast: ScriptAST, ctx: RuntimeContext) -> None:
    hooks = step.get("on_fail")
    if hooks is None:
        return
    if not isinstance(hooks, list):
        raise ValueError("step.on_fail must be a list")
    for idx, hook in enumerate(hooks):
        if not isinstance(hook, dict):
            raise ValueError(f"step.on_fail[{idx}] must be a mapping")
        try:
            _dispatch_step(hook, ast, ctx)
        except Exception as exc:
            ctx.logger.warning(f"on_fail step ignored due to error: {exc}")


def _run_step_with_reliability(step: Dict[str, Any], ast: ScriptAST, ctx: RuntimeContext) -> None:
    retry = _resolve_retry(step, ast)
    count = int(retry["count"])
    backoff_ms = int(retry["backoff_ms"])
    strategy = str(retry["strategy"])
    last_error: Exception | None = None

    for attempt in range(count + 1):
        try:
            _dispatch_step(step, ast, ctx)
            return
        except Exception as exc:
            last_error = exc
            if attempt >= count:
                break
            delay_ms = backoff_ms if strategy == "fixed" else backoff_ms * (2**attempt)
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)

    try:
        _run_on_fail(step, ast, ctx)
    finally:
        if last_error is not None:
            raise last_error


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
            _run_step_with_reliability(step, ast, ctx)
            trace["status"] = "ok"
        except Exception as exc:
            trace["status"] = "error"
            trace["error"] = {"code": type(exc).__name__, "message": str(exc)}
            error = {"code": type(exc).__name__, "message": str(exc), "step_id": step_id}
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
