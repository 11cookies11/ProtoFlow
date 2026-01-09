from __future__ import annotations

import time
from typing import Any, Dict

from actions.registry import ActionRegistry
from dsl.expression import eval_expr


def _eval(ctx, val):
    if isinstance(val, str) and "$" in val:
        return eval_expr(val, ctx.vars_snapshot())
    return val


def action_set(ctx, args: Dict[str, Any]):
    for key, val in args.items():
        ctx.set_var(key, _eval(ctx, val))
    return ctx.vars_snapshot()


def action_log(ctx, args: Dict[str, Any]):
    msg = args.get("message") or args.get("msg") or ""
    if isinstance(msg, str) and "$" in msg:
        msg = eval_expr(msg, ctx.vars_snapshot())
    ctx.logger.info(str(msg))


def action_wait(ctx, args: Dict[str, Any]):
    ms = int(args.get("ms", 0))
    time.sleep(ms / 1000.0)


def action_wait_for_event(ctx, args: Dict[str, Any]):
    expected = args.get("event")
    timeout = float(args.get("timeout", 1.0))
    end = time.time() + timeout
    while time.time() < end:
        evt = ctx.next_event(timeout=0.1)
        if evt is None:
            continue
        if expected is None or evt == expected:
            ctx.set_var("event", evt)
            return evt
    return None


def register_builtin_actions():
    ActionRegistry.register("set", action_set)
    ActionRegistry.register("log", action_log)
    ActionRegistry.register("send_text", action_send_text)
    ActionRegistry.register("read_line", action_read_line)
    ActionRegistry.register("read_stream", action_read_stream)
    ActionRegistry.register("wait", action_wait)
    ActionRegistry.register("wait_for_event", action_wait_for_event)


def action_send_text(ctx, args: Dict[str, Any]):
    text = args.get("text", args.get("data", ""))
    if isinstance(text, (bytes, bytearray)):
        payload = bytes(text)
    else:
        payload = str(text)
    append_cr = bool(args.get("append_cr", False))
    append_lf = bool(args.get("append_lf", False))
    if append_cr:
        payload = payload + (b"\r" if isinstance(payload, (bytes, bytearray)) else "\r")
    if append_lf:
        payload = payload + (b"\n" if isinstance(payload, (bytes, bytearray)) else "\n")
    ctx.channel_write(payload)
    return {"text": text, "append_cr": append_cr, "append_lf": append_lf}


def action_read_line(ctx, args: Dict[str, Any]):
    terminator = args.get("terminator", "\n")
    timeout = float(args.get("timeout", 1.0))
    raw = ctx.channel.read_until(
        terminator.encode() if isinstance(terminator, str) else bytes(terminator),
        timeout=timeout,
    )
    text = raw.decode(errors="ignore").strip()
    ctx.set_var("last_line_rx", text)
    ctx.set_var("last_line_rx_raw", raw.hex().upper())
    return {"text": text, "hex": raw.hex().upper()}


def action_read_stream(ctx, args: Dict[str, Any]):
    duration_ms = int(args.get("duration_ms", args.get("duration", 1000)))
    chunk_size = int(args.get("chunk_size", 256))
    timeout = float(args.get("timeout", 0.2))
    log_hex = bool(args.get("log_hex", True))
    end = time.time() + max(0.0, duration_ms / 1000.0)
    last_text = ""
    last_hex = ""
    while time.time() < end:
        chunk = ctx.channel.read(chunk_size, timeout=timeout)
        if not chunk:
            continue
        last_hex = chunk.hex().upper()
        try:
            last_text = chunk.decode(errors="ignore")
        except Exception:
            last_text = ""
        if log_hex:
            ctx.logger.info(f"RX(hex): {last_hex}")
        if last_text.strip():
            ctx.logger.info(f"RX(text): {last_text.strip()}")
    ctx.set_var("last_stream_rx", last_text.strip())
    ctx.set_var("last_stream_rx_raw", last_hex)
    return {"text": last_text.strip(), "hex": last_hex}
