from __future__ import annotations

import re
import time
from typing import Any, Dict

from dsl_runtime.lang.ast_nodes import ScriptAST
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
    env.update(ast.params or {})
    env.update(ast.vars_snapshot())
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
            return

    raise TimeoutError("expect timeout: match not found")


def _run_sleep_step(step: Dict[str, Any]) -> None:
    ms = int(step.get("ms", 0))
    if ms < 0:
        raise ValueError("sleep.ms must be >= 0")
    if ms == 0:
        return
    time.sleep(ms / 1000.0)


def execute_v01(ast: ScriptAST, ctx: RuntimeContext) -> None:
    for idx, step in enumerate(ast.steps):
        name = str(step.get("name", "")).strip().lower()
        if not name:
            raise ValueError(f"steps[{idx}].name is required")
        if name == "send":
            _run_send_step(step, ast, ctx)
            continue
        if name == "expect":
            _run_expect_step(step, ast, ctx)
            continue
        if name == "sleep":
            _run_sleep_step(step)
            continue
        raise NotImplementedError(f"v0.1 step not implemented yet: {name}")
