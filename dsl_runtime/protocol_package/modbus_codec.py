from __future__ import annotations

from typing import Any, Dict, List


_OP_TO_FC = {
    "read_holding": 0x03,
    "read_input": 0x04,
    "write_single_coil": 0x05,
    "write_single_register": 0x06,
    "write_multiple_coils": 0x0F,
    "write_multiple_registers": 0x10,
}


def modbus_fail(code: str, message: str) -> None:
    raise ValueError(f"{code}: {message}")


def operation_to_fc(op: str) -> int:
    key = str(op or "").strip().lower()
    if key not in _OP_TO_FC:
        modbus_fail("MODBUS_FUNCTION_UNSUPPORTED", f"unsupported operation: {op}")
    return int(_OP_TO_FC[key])


def _u16(value: Any, *, field: str) -> int:
    iv = int(value)
    if iv < 0 or iv > 0xFFFF:
        modbus_fail("MODBUS_VALUE_INVALID", f"{field} out of range: {iv}")
    return iv


def _as_bool_list(values: Any) -> List[bool]:
    if not isinstance(values, list) or not values:
        modbus_fail("MODBUS_VALUE_INVALID", "values must be a non-empty list")
    out: List[bool] = []
    for i, item in enumerate(values):
        if isinstance(item, bool):
            out.append(item)
            continue
        if isinstance(item, int):
            out.append(item != 0)
            continue
        modbus_fail("MODBUS_VALUE_INVALID", f"values[{i}] must be bool/int")
    return out


def _pack_coils(values: List[bool]) -> bytes:
    out = bytearray((len(values) + 7) // 8)
    for i, bit in enumerate(values):
        if bit:
            out[i // 8] |= 1 << (i % 8)
    return bytes(out)


def _unpack_coils(payload: bytes, quantity: int) -> List[bool]:
    out: List[bool] = []
    for i in range(quantity):
        out.append(((payload[i // 8] >> (i % 8)) & 0x01) == 1)
    return out


def encode_request_pdu(request: Dict[str, Any]) -> bytes:
    op = str(request.get("op", "")).strip().lower()
    fc = operation_to_fc(op)
    address = _u16(request.get("address"), field="address")

    if fc in {0x03, 0x04}:
        quantity = _u16(request.get("quantity"), field="quantity")
        if quantity <= 0 or quantity > 0x007D:
            modbus_fail("MODBUS_VALUE_INVALID", "quantity out of range for read")
        return bytes([fc]) + address.to_bytes(2, "big") + quantity.to_bytes(2, "big")

    if fc == 0x05:
        value = request.get("value")
        coil = 0xFF00 if bool(value) else 0x0000
        return bytes([fc]) + address.to_bytes(2, "big") + coil.to_bytes(2, "big")

    if fc == 0x06:
        value = _u16(request.get("value"), field="value")
        return bytes([fc]) + address.to_bytes(2, "big") + value.to_bytes(2, "big")

    if fc == 0x0F:
        values = _as_bool_list(request.get("values"))
        quantity = len(values)
        if quantity <= 0 or quantity > 0x07B0:
            modbus_fail("MODBUS_VALUE_INVALID", "coil quantity out of range")
        packed = _pack_coils(values)
        return (
            bytes([fc])
            + address.to_bytes(2, "big")
            + quantity.to_bytes(2, "big")
            + bytes([len(packed)])
            + packed
        )

    if fc == 0x10:
        values_any = request.get("values")
        if not isinstance(values_any, list) or not values_any:
            modbus_fail("MODBUS_VALUE_INVALID", "values must be a non-empty list")
        values = [_u16(v, field="values") for v in values_any]
        quantity = len(values)
        if quantity <= 0 or quantity > 0x007B:
            modbus_fail("MODBUS_VALUE_INVALID", "register quantity out of range")
        payload = b"".join(v.to_bytes(2, "big") for v in values)
        return (
            bytes([fc])
            + address.to_bytes(2, "big")
            + quantity.to_bytes(2, "big")
            + bytes([len(payload)])
            + payload
        )

    modbus_fail("MODBUS_FUNCTION_UNSUPPORTED", f"unsupported function: {fc}")
    return b""


def decode_response_pdu(function: int, pdu: bytes, *, quantity: int | None = None) -> Dict[str, Any]:
    if not pdu:
        modbus_fail("MODBUS_FRAME_INVALID", "empty pdu")
    fc = pdu[0]
    if fc == (function | 0x80):
        if len(pdu) < 2:
            modbus_fail("MODBUS_FRAME_INVALID", "exception response too short")
        return {
            "ok": False,
            "error": {
                "code": "MODBUS_EXCEPTION_RESPONSE",
                "message": f"modbus exception code {pdu[1]}",
                "exception_code": int(pdu[1]),
            },
            "function": function,
        }
    if fc != function:
        modbus_fail("MODBUS_FRAME_INVALID", f"function mismatch: expect {function}, got {fc}")

    if function in {0x03, 0x04}:
        if len(pdu) < 2:
            modbus_fail("MODBUS_FRAME_INVALID", "read response too short")
        byte_count = int(pdu[1])
        payload = pdu[2:]
        if byte_count != len(payload):
            modbus_fail("MODBUS_FRAME_INVALID", "byte_count mismatch")
        if byte_count % 2 != 0:
            modbus_fail("MODBUS_FRAME_INVALID", "register payload byte_count must be even")
        registers = [int.from_bytes(payload[i : i + 2], "big") for i in range(0, len(payload), 2)]
        return {"ok": True, "function": function, "data": {"registers": registers}}

    if function == 0x05:
        if len(pdu) != 5:
            modbus_fail("MODBUS_FRAME_INVALID", "FC05 response length must be 5")
        addr = int.from_bytes(pdu[1:3], "big")
        raw = int.from_bytes(pdu[3:5], "big")
        return {"ok": True, "function": function, "data": {"address": addr, "value": raw == 0xFF00}}

    if function == 0x06:
        if len(pdu) != 5:
            modbus_fail("MODBUS_FRAME_INVALID", "FC06 response length must be 5")
        addr = int.from_bytes(pdu[1:3], "big")
        val = int.from_bytes(pdu[3:5], "big")
        return {"ok": True, "function": function, "data": {"address": addr, "value": val}}

    if function == 0x0F:
        if len(pdu) != 5:
            modbus_fail("MODBUS_FRAME_INVALID", "FC15 response length must be 5")
        addr = int.from_bytes(pdu[1:3], "big")
        qty = int.from_bytes(pdu[3:5], "big")
        return {"ok": True, "function": function, "data": {"address": addr, "quantity": qty}}

    if function == 0x10:
        if len(pdu) != 5:
            modbus_fail("MODBUS_FRAME_INVALID", "FC16 response length must be 5")
        addr = int.from_bytes(pdu[1:3], "big")
        qty = int.from_bytes(pdu[3:5], "big")
        return {"ok": True, "function": function, "data": {"address": addr, "quantity": qty}}

    if function == 0x01:
        if len(pdu) < 2:
            modbus_fail("MODBUS_FRAME_INVALID", "FC01 response too short")
        byte_count = int(pdu[1])
        payload = pdu[2:]
        if byte_count != len(payload):
            modbus_fail("MODBUS_FRAME_INVALID", "byte_count mismatch")
        q = int(quantity or (byte_count * 8))
        return {"ok": True, "function": function, "data": {"coils": _unpack_coils(payload, q)}}

    modbus_fail("MODBUS_FUNCTION_UNSUPPORTED", f"decode not supported for function: {function}")
    return {}
