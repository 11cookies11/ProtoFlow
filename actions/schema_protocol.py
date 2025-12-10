from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict

from actions.registry import ActionRegistry
from protocols.schema_runtime import ProtocolSchema


@lru_cache(maxsize=16)
def _load_schema(path: str) -> ProtocolSchema:
    return ProtocolSchema.load(path)


def action_send_frame(ctx, args: Dict[str, Any]):
    schema_path = args.get("schema")
    frame = args.get("frame")
    if not schema_path or not frame:
        raise ValueError("send_frame requires schema and frame")
    values = {k: ctx.eval_value(v) for k, v in (args.get("values") or {}).items()}
    schema = _load_schema(str(schema_path))
    packet = schema.build(frame, values)
    ctx.channel_write(packet)
    ctx.set_var("last_frame_tx", {"frame": frame, "values": values, "hex": packet.hex().upper()})
    return packet


def action_expect_frame(ctx, args: Dict[str, Any]):
    schema_path = args.get("schema")
    frame = args.get("frame")
    timeout = float(args.get("timeout", 2.0))
    save_as = args.get("save_as", "last_frame_rx")
    if not schema_path or not frame:
        raise ValueError("expect_frame requires schema and frame")

    schema = _load_schema(str(schema_path))
    fd = schema.frames.get(frame)
    if fd is None:
        raise KeyError(f"unknown frame: {frame}")

    data = b""
    if fd.tail:
        data = ctx.channel.read_until(fd.tail, timeout=timeout)
    else:
        fixed = fd.fixed_length()
        if fixed is None:
            raise ValueError("expect_frame requires tail or fixed frame length")
        data = ctx.channel.read_exact(fixed, timeout=timeout)  # type: ignore[attr-defined]

    if not data:
        raise TimeoutError("expect_frame timeout")

    parsed = schema.parse(frame, data)
    ctx.set_var(save_as, parsed)
    ctx.set_var("last_frame_rx_raw", data.hex().upper())
    return parsed


def register_schema_protocol_actions() -> None:
    ActionRegistry.register("send_frame", action_send_frame)
    ActionRegistry.register("expect_frame", action_expect_frame)
