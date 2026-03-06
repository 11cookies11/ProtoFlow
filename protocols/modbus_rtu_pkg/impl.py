from __future__ import annotations

from typing import Any, Dict

from dsl_runtime.protocol_package.modbus_codec import decode_response_pdu, encode_request_pdu, operation_to_fc


def _crc16_modbus(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc & 0xFFFF


def _build_frame(unit: int, pdu: bytes) -> bytes:
    body = bytes([unit & 0xFF]) + pdu
    crc = _crc16_modbus(body)
    return body + bytes([crc & 0xFF, (crc >> 8) & 0xFF])


def _parse_rtu_frame(frame: bytes) -> Dict[str, Any]:
    if len(frame) < 5:
        raise ValueError("MODBUS_FRAME_INVALID: frame too short")
    body = frame[:-2]
    crc_rx = int.from_bytes(frame[-2:], "little")
    crc_calc = _crc16_modbus(body)
    if crc_calc != crc_rx:
        raise ValueError("MODBUS_CRC_INVALID: crc mismatch")
    return {"unit_id": int(frame[0]), "pdu": frame[1:-2], "rx_hex": frame.hex().upper()}


class ProtocolPackage:
    def send(self, ctx, request: Dict[str, Any]) -> Dict[str, Any]:
        unit = int(request.get("unit_id", request.get("unit", 1)))
        pdu = encode_request_pdu(request)
        frame = _build_frame(unit, pdu)
        ctx.channel.write(frame)
        return {
            "ok": True,
            "unit_id": unit,
            "function": int(pdu[0]),
            "raw": {"tx_hex": frame.hex().upper()},
            "size": len(frame),
        }

    def recv(self, ctx, expect: Dict[str, Any]) -> Dict[str, Any]:
        expected_size = int(expect.get("size", 256))
        rx = ctx.channel.read(expected_size, timeout=max(0.01, ctx.timeout_ms / 1000.0))
        if not rx:
            raise TimeoutError("MODBUS_TIMEOUT: no response bytes")
        parsed = _parse_rtu_frame(rx)

        op = str(expect.get("op", "")).strip().lower()
        function = int(expect.get("function", operation_to_fc(op) if op else parsed["pdu"][0]))
        quantity = expect.get("quantity")
        decoded = decode_response_pdu(function, parsed["pdu"], quantity=quantity)
        decoded["unit_id"] = parsed["unit_id"]
        decoded["raw"] = {"rx_hex": parsed["rx_hex"]}
        decoded["size"] = len(rx)
        return decoded

    def rpc(self, ctx, request: Dict[str, Any]) -> Dict[str, Any]:
        tx = self.send(ctx, request)
        rx_expect = dict(request.get("expect") or {})
        if not isinstance(rx_expect, dict):
            rx_expect = {}
        if "op" not in rx_expect and "op" in request:
            rx_expect["op"] = request.get("op")
        if "quantity" not in rx_expect and "quantity" in request:
            rx_expect["quantity"] = request.get("quantity")
        if "function" not in rx_expect and "function" in tx:
            rx_expect["function"] = tx.get("function")
        rx = self.recv(ctx, rx_expect)
        out: Dict[str, Any] = {"ok": bool(rx.get("ok", True))}
        out.update(rx)
        out["raw"] = {"tx_hex": tx.get("raw", {}).get("tx_hex"), "rx_hex": rx.get("raw", {}).get("rx_hex")}
        return out
