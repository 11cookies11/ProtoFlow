from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict

from dsl_runtime.actions.base import DslActionBase
from dsl_runtime.actions.registry import ActionRegistry
from infra.protocol.schema_runtime import ProtocolSchema


@lru_cache(maxsize=16)
def _load_schema(path: str) -> ProtocolSchema:
    return ProtocolSchema.load(path)


class SendFrameAction(DslActionBase):
    def __init__(self) -> None:
        super().__init__(
            name="send_frame",
            schema={
                "required": ["schema", "frame"],
                "optional": {"values": {}},
                "types": {"values": "mapping"},
                "allow_extra": False,
            },
        )

    def execute(self, ctx, args: Dict[str, Any]):
        schema_path = args.get("schema")
        frame = args.get("frame")
        values = {k: ctx.eval_value(v) for k, v in (args.get("values") or {}).items()}
        schema = _load_schema(str(schema_path))
        packet = schema.build(frame, values)
        ctx.channel_write(packet)
        ctx.set_var("last_frame_tx", {"frame": frame, "values": values, "hex": packet.hex().upper()})
        return packet


class ExpectFrameAction(DslActionBase):
    def __init__(self) -> None:
        super().__init__(
            name="expect_frame",
            schema={
                "required": ["schema", "frame"],
                "optional": {"timeout": 2.0, "save_as": "last_frame_rx"},
                "types": {"timeout": "number"},
                "allow_extra": False,
            },
        )

    def execute(self, ctx, args: Dict[str, Any]):
        schema_path = args.get("schema")
        frame = args.get("frame")
        timeout = float(args.get("timeout", 2.0))
        save_as = args.get("save_as", "last_frame_rx")

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
    ActionRegistry.register("send_frame", SendFrameAction())
    ActionRegistry.register("expect_frame", ExpectFrameAction())
