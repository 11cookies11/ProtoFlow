from __future__ import annotations

import re
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


def execute_v01(ast: ScriptAST, ctx: RuntimeContext) -> None:
    for idx, step in enumerate(ast.steps):
        name = str(step.get("name", "")).strip().lower()
        if not name:
            raise ValueError(f"steps[{idx}].name is required")
        if name == "send":
            _run_send_step(step, ast, ctx)
            continue
        raise NotImplementedError(f"v0.1 step not implemented yet: {name}")
