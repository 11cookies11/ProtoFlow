from __future__ import annotations

import time
from typing import Any, Dict

from actions.dsl.base import DslActionBase
from actions.registry import ActionRegistry
from dsl.expression import eval_expr


def _eval(ctx, val):
    if isinstance(val, str) and "$" in val:
        return eval_expr(val, ctx.vars_snapshot())
    return val


class SetAction(DslActionBase):
    def __init__(self) -> None:
        super().__init__(
            name="set",
            schema={
                "allow_extra": True,
            },
        )

    def execute(self, ctx, args: Dict[str, Any]):
        for key, val in args.items():
            ctx.set_var(key, _eval(ctx, val))
        return ctx.vars_snapshot()


class LogAction(DslActionBase):
    def __init__(self) -> None:
        super().__init__(
            name="log",
            schema={
                "aliases": {"msg": "message"},
                "optional": {"message": ""},
                "types": {"message": (str, int, float, bool, bytes, bytearray)},
                "allow_extra": False,
            },
        )

    def execute(self, ctx, args: Dict[str, Any]):
        msg = args.get("message") or ""
        if isinstance(msg, str) and "$" in msg:
            msg = eval_expr(msg, ctx.vars_snapshot())
        ctx.logger.info(str(msg))


class WaitAction(DslActionBase):
    def __init__(self) -> None:
        super().__init__(
            name="wait",
            schema={
                "optional": {"ms": 0},
                "types": {"ms": "number"},
                "allow_extra": False,
            },
        )

    def execute(self, ctx, args: Dict[str, Any]):
        ms = int(args.get("ms", 0))
        time.sleep(ms / 1000.0)


class WaitForEventAction(DslActionBase):
    def __init__(self) -> None:
        super().__init__(
            name="wait_for_event",
            schema={
                "optional": {"event": None, "timeout": 1.0},
                "types": {"timeout": "number"},
                "allow_extra": False,
            },
        )

    def execute(self, ctx, args: Dict[str, Any]):
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


class SendTextAction(DslActionBase):
    def __init__(self) -> None:
        super().__init__(
            name="send_text",
            schema={
                "aliases": {"data": "text"},
                "optional": {"text": "", "append_cr": False, "append_lf": False},
                "types": {"append_cr": bool, "append_lf": bool},
                "allow_extra": False,
            },
        )

    def execute(self, ctx, args: Dict[str, Any]):
        text = args.get("text", "")
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


class ReadLineAction(DslActionBase):
    def __init__(self) -> None:
        super().__init__(
            name="read_line",
            schema={
                "optional": {"terminator": "\n", "timeout": 1.0},
                "types": {"timeout": "number"},
                "allow_extra": False,
            },
        )

    def execute(self, ctx, args: Dict[str, Any]):
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


class ReadStreamAction(DslActionBase):
    def __init__(self) -> None:
        super().__init__(
            name="read_stream",
            schema={
                "aliases": {"duration": "duration_ms"},
                "optional": {
                    "duration_ms": 1000,
                    "chunk_size": 256,
                    "timeout": 0.2,
                    "log_hex": True,
                },
                "types": {
                    "duration_ms": "number",
                    "chunk_size": "number",
                    "timeout": "number",
                    "log_hex": bool,
                },
                "allow_extra": False,
            },
        )

    def execute(self, ctx, args: Dict[str, Any]):
        duration_ms = int(args.get("duration_ms", 1000))
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


def register_builtin_actions() -> None:
    ActionRegistry.register("set", SetAction())
    ActionRegistry.register("log", LogAction())
    ActionRegistry.register("send_text", SendTextAction())
    ActionRegistry.register("read_line", ReadLineAction())
    ActionRegistry.register("read_stream", ReadStreamAction())
    ActionRegistry.register("wait", WaitAction())
    ActionRegistry.register("wait_for_event", WaitForEventAction())
