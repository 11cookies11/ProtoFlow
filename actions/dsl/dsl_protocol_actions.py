from __future__ import annotations

from typing import Dict

from actions.dsl.base import DslActionBase
from actions.registry import ActionRegistry
from protocols.registry import ProtocolRegistry
from protocols import modbus_ascii, modbus_rtu, modbus_tcp  # noqa: F401
from utils.crc16 import crc16_xmodem
from utils.file_utils import get_file_meta, read_block


class XMODEMPacketBuilder:
    @staticmethod
    def build_block(block_no: int, data: bytes, use_crc: bool = True) -> bytes:
        data128 = data[:128] if len(data) >= 128 else data + b"\x1A" * (128 - len(data))
        header = bytes([0x01, block_no & 0xFF, 0xFF - (block_no & 0xFF)])
        if use_crc:
            crc = crc16_xmodem(data128).to_bytes(2, "big")
            return header + data128 + crc
        checksum = sum(data128) & 0xFF
        return header + data128 + bytes([checksum])

    @staticmethod
    def build_eot() -> bytes:
        return bytes([0x04])


class SendXmodemBlockAction(DslActionBase):
    def __init__(self) -> None:
        super().__init__(
            name="send_xmodem_block",
            schema={
                "optional": {"block": 1},
                "types": {"block": "number"},
                "allow_extra": False,
            },
        )

    def execute(self, ctx, args: Dict[str, object]):
        meta = get_file_meta(ctx)
        ctx.set_var("file", meta)
        ctx.set_var("file.block_count", meta.get("block_count"))
        ctx.set_var("file.size", meta.get("size"))
        ctx.set_var("file_block_count", meta.get("block_count"))
        ctx.set_var("file_size", meta.get("size"))
        block = int(ctx.eval_value(args.get("block", 1)))
        data = read_block(meta["path"], block, 128)
        packet = XMODEMPacketBuilder.build_block(block, data)
        ctx.channel_write(packet)
        ctx.set_var("last_sent_block", block)


class SendEotAction(DslActionBase):
    def __init__(self) -> None:
        super().__init__(
            name="send_eot",
            schema={
                "allow_extra": False,
            },
        )

    def execute(self, ctx, args: Dict[str, object]):
        ctx.channel_write(XMODEMPacketBuilder.build_eot())


_MODBUS_MAP = {
    "rtu": "modbus_rtu",
    "ascii": "modbus_ascii",
    "tcp": "modbus_tcp",
}


def _eval_arg(ctx, value):
    if isinstance(value, (list, tuple)):
        return [ctx.eval_value(item) for item in value]
    return ctx.eval_value(value)


def _coerce_values(values):
    if values is None:
        return None
    if isinstance(values, (list, tuple, bytes, bytearray)):
        return values
    return [values]


def _resolve_modbus_channel(ctx, args: Dict[str, object]):
    channel_name = args.get("channel")
    if channel_name:
        channel_name = _eval_arg(ctx, channel_name)
        if channel_name not in ctx.channels:
            raise KeyError(f"channel not found: {channel_name}")
        return ctx.channels[channel_name]
    return ctx.channel


def _resolve_modbus_protocol(ctx, args: Dict[str, object]):
    proto = str(_eval_arg(ctx, args.get("protocol", "rtu"))).lower()
    protocol_key = _MODBUS_MAP.get(proto)
    if not protocol_key:
        raise ValueError("modbus_* protocol must be rtu / ascii / tcp")
    return protocol_key


def _run_modbus(ctx, args: Dict[str, object]):
    protocol_key = _resolve_modbus_protocol(ctx, args)
    channel = _resolve_modbus_channel(ctx, args)
    protocol_cls = ProtocolRegistry.get(protocol_key)
    protocol = protocol_cls(channel, ctx.logger)

    function = int(_eval_arg(ctx, args.get("function", 3)))
    address = int(_eval_arg(ctx, args.get("address", 0)))
    quantity = args.get("quantity")
    values = _eval_arg(ctx, args.get("values", args.get("value")))
    values = _coerce_values(values)
    unit_id = int(_eval_arg(ctx, args.get("unit_id", 1)))

    if quantity is None:
        quantity = len(values) if isinstance(values, (list, tuple)) else 1
    quantity = int(_eval_arg(ctx, quantity))

    if protocol_key == "modbus_tcp":
        timeout_s = float(_eval_arg(ctx, args.get("timeout", 2.0)))
        result = protocol.execute(
            function=function,
            address=address,
            quantity=quantity,
            values=values,
            unit_id=unit_id,
            timeout=timeout_s,
        )
    else:
        retries = int(_eval_arg(ctx, args.get("retries", 3)))
        timeout_ms = int(_eval_arg(ctx, args.get("timeout", 1000)))
        result = protocol.execute(
            function=function,
            address=address,
            quantity=quantity,
            values=values,
            unit_id=unit_id,
            retries=retries,
            timeout=timeout_ms,
        )

    ctx.set_var("last_modbus", result)
    save_as = args.get("save_as")
    if save_as:
        ctx.set_var(str(save_as), result)
    return result


class ModbusReadAction(DslActionBase):
    def __init__(self) -> None:
        super().__init__(
            name="modbus_read",
            schema={
                "required": ["function", "address"],
                "optional": {
                    "protocol": "rtu",
                    "channel": None,
                    "quantity": None,
                    "values": None,
                    "value": None,
                    "unit_id": 1,
                    "timeout": None,
                    "retries": 3,
                    "save_as": None,
                },
                "allow_extra": False,
            },
        )

    def execute(self, ctx, args: Dict[str, object]):
        return _run_modbus(ctx, args)


class ModbusWriteAction(DslActionBase):
    def __init__(self) -> None:
        super().__init__(
            name="modbus_write",
            schema={
                "required": ["function", "address"],
                "optional": {
                    "protocol": "rtu",
                    "channel": None,
                    "quantity": None,
                    "values": None,
                    "value": None,
                    "unit_id": 1,
                    "timeout": None,
                    "retries": 3,
                    "save_as": None,
                },
                "allow_extra": False,
            },
        )

    def execute(self, ctx, args: Dict[str, object]):
        return _run_modbus(ctx, args)


def register_protocol_actions():
    ActionRegistry.register("send_xmodem_block", SendXmodemBlockAction())
    ActionRegistry.register("send_eot", SendEotAction())
    ActionRegistry.register("modbus_read", ModbusReadAction())
    ActionRegistry.register("modbus_write", ModbusWriteAction())
