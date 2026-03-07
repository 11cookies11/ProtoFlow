from __future__ import annotations

from typing import Any, Dict

from dsl_runtime.protocol_package.modbus_codec import decode_response_pdu, encode_request_pdu, operation_to_fc


def _build_mbap(transaction_id: int, unit_id: int, pdu_len: int) -> bytes:
    protocol_id = 0
    length = pdu_len + 1
    return (
        int(transaction_id & 0xFFFF).to_bytes(2, "big")
        + int(protocol_id).to_bytes(2, "big")
        + int(length).to_bytes(2, "big")
        + bytes([unit_id & 0xFF])
    )


def _parse_mbap(frame: bytes) -> Dict[str, Any]:
    if len(frame) < 8:
        raise ValueError("MODBUS_MBAP_INVALID: frame too short")
    tid = int.from_bytes(frame[0:2], "big")
    pid = int.from_bytes(frame[2:4], "big")
    length = int.from_bytes(frame[4:6], "big")
    unit = int(frame[6])
    pdu = frame[7:]
    if pid != 0:
        raise ValueError("MODBUS_MBAP_INVALID: protocol_id must be 0")
    if length != len(pdu) + 1:
        raise ValueError("MODBUS_MBAP_INVALID: length mismatch")
    if not pdu:
        raise ValueError("MODBUS_FRAME_INVALID: empty pdu")
    return {"transaction_id": tid, "unit_id": unit, "pdu": pdu, "rx_hex": frame.hex().upper()}


class ProtocolPackage:
    def __init__(self) -> None:
        self._next_tid = 1

    def _alloc_tid(self, request: Dict[str, Any]) -> int:
        if "transaction_id" in request:
            return int(request.get("transaction_id")) & 0xFFFF
        tid = self._next_tid
        self._next_tid = (self._next_tid + 1) & 0xFFFF
        return tid

    def send(self, ctx, request: Dict[str, Any]) -> Dict[str, Any]:
        unit = int(request.get("unit_id", request.get("unit", 1)))
        tid = self._alloc_tid(request)
        pdu = encode_request_pdu(request)
        frame = _build_mbap(tid, unit, len(pdu)) + pdu
        ctx.channel.write(frame)
        return {
            "ok": True,
            "transaction_id": tid,
            "unit_id": unit,
            "function": int(pdu[0]),
            "raw": {"tx_hex": frame.hex().upper()},
            "size": len(frame),
        }

    def recv(self, ctx, expect: Dict[str, Any]) -> Dict[str, Any]:
        size = int(expect.get("size", 260))
        rx = ctx.channel.read(size, timeout=max(0.01, ctx.timeout_ms / 1000.0))
        if not rx:
            raise TimeoutError("MODBUS_TIMEOUT: no response bytes")
        parsed = _parse_mbap(rx)
        op = str(expect.get("op", "")).strip().lower()
        function = int(expect.get("function", operation_to_fc(op) if op else parsed["pdu"][0]))
        quantity = expect.get("quantity")
        decoded = decode_response_pdu(function, parsed["pdu"], quantity=quantity)
        decoded["transaction_id"] = parsed["transaction_id"]
        decoded["unit_id"] = parsed["unit_id"]
        decoded["raw"] = {"rx_hex": parsed["rx_hex"]}
        decoded["size"] = len(rx)
        return decoded

    def rpc(self, ctx, request: Dict[str, Any]) -> Dict[str, Any]:
        tx = self.send(ctx, request)
        rx_expect = dict(request.get("expect") or {})
        if "op" not in rx_expect and "op" in request:
            rx_expect["op"] = request.get("op")
        if "quantity" not in rx_expect and "quantity" in request:
            rx_expect["quantity"] = request.get("quantity")
        if "function" not in rx_expect and "function" in tx:
            rx_expect["function"] = tx.get("function")
        if "transaction_id" not in rx_expect and "transaction_id" in tx:
            rx_expect["transaction_id"] = tx.get("transaction_id")
        rx = self.recv(ctx, rx_expect)
        out: Dict[str, Any] = {"ok": bool(rx.get("ok", True))}
        out.update(rx)
        out["raw"] = {"tx_hex": tx.get("raw", {}).get("tx_hex"), "rx_hex": rx.get("raw", {}).get("rx_hex")}
        return out
