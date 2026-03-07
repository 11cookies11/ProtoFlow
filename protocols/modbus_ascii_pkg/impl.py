from __future__ import annotations

from typing import Any, Dict

from dsl_runtime.protocol_package.modbus_codec import decode_response_pdu, encode_request_pdu, operation_to_fc


def _calc_lrc(data: bytes) -> int:
    return ((-sum(data)) & 0xFF)


def _to_ascii_frame(unit_id: int, pdu: bytes) -> bytes:
    body = bytes([unit_id & 0xFF]) + pdu
    lrc = _calc_lrc(body)
    text = ":" + (body + bytes([lrc])).hex().upper() + "\r\n"
    return text.encode("ascii")


def _parse_ascii_frame(frame: bytes) -> Dict[str, Any]:
    text = frame.decode("ascii", errors="ignore").strip()
    if not text.startswith(":"):
        raise ValueError("MODBUS_FRAME_INVALID: ascii frame must start with ':'")
    hex_text = text[1:]
    if len(hex_text) < 6 or len(hex_text) % 2 != 0:
        raise ValueError("MODBUS_FRAME_INVALID: invalid ascii hex length")
    raw = bytes.fromhex(hex_text)
    if len(raw) < 3:
        raise ValueError("MODBUS_FRAME_INVALID: ascii payload too short")
    body = raw[:-1]
    lrc_rx = int(raw[-1])
    lrc_calc = _calc_lrc(body)
    if lrc_rx != lrc_calc:
        raise ValueError("MODBUS_LRC_INVALID: lrc mismatch")
    return {"unit_id": int(body[0]), "pdu": body[1:], "rx_hex": raw.hex().upper(), "rx_text": text}


class ProtocolPackage:
    def send(self, ctx, request: Dict[str, Any]) -> Dict[str, Any]:
        unit = int(request.get("unit_id", request.get("unit", 1)))
        pdu = encode_request_pdu(request)
        frame = _to_ascii_frame(unit, pdu)
        ctx.channel.write(frame)
        return {
            "ok": True,
            "unit_id": unit,
            "function": int(pdu[0]),
            "raw": {"tx_ascii": frame.decode("ascii", errors="ignore").strip(), "tx_hex": frame.hex().upper()},
            "size": len(frame),
        }

    def recv(self, ctx, expect: Dict[str, Any]) -> Dict[str, Any]:
        size = int(expect.get("size", 512))
        rx = ctx.channel.read(size, timeout=max(0.01, ctx.timeout_ms / 1000.0))
        if not rx:
            raise TimeoutError("MODBUS_TIMEOUT: no response bytes")
        parsed = _parse_ascii_frame(rx)
        op = str(expect.get("op", "")).strip().lower()
        function = int(expect.get("function", operation_to_fc(op) if op else parsed["pdu"][0]))
        quantity = expect.get("quantity")
        decoded = decode_response_pdu(function, parsed["pdu"], quantity=quantity)
        decoded["unit_id"] = parsed["unit_id"]
        decoded["raw"] = {"rx_ascii": parsed["rx_text"], "rx_hex": parsed["rx_hex"]}
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
        rx = self.recv(ctx, rx_expect)
        out: Dict[str, Any] = {"ok": bool(rx.get("ok", True))}
        out.update(rx)
        out["raw"] = {"tx_ascii": tx.get("raw", {}).get("tx_ascii"), "rx_ascii": rx.get("raw", {}).get("rx_ascii")}
        return out
