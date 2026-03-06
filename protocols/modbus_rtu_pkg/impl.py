from __future__ import annotations

from typing import Any, Dict


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


def _build_frame(unit: int, function: int, payload_hex: str) -> bytes:
    body = bytes([unit & 0xFF, function & 0xFF]) + bytes.fromhex(payload_hex.replace(" ", ""))
    crc = _crc16_modbus(body)
    return body + bytes([crc & 0xFF, (crc >> 8) & 0xFF])


class ProtocolPackage:
    def send(self, ctx, request: Dict[str, Any]) -> Dict[str, Any]:
        unit = int(request.get("unit", 1))
        function = int(request.get("function", 3))
        payload_hex = str(request.get("payload_hex", "")).strip()
        frame = _build_frame(unit, function, payload_hex)
        ctx.channel.write(frame)
        return {"tx_hex": frame.hex().upper(), "size": len(frame)}

    def recv(self, ctx, expect: Dict[str, Any]) -> Dict[str, Any]:
        size = int(expect.get("size", 256))
        rx = ctx.channel.read(size, timeout=max(0.01, ctx.timeout_ms / 1000.0))
        if not rx:
            raise TimeoutError("no response bytes")
        return {"rx_hex": rx.hex().upper(), "size": len(rx)}

    def rpc(self, ctx, request: Dict[str, Any]) -> Dict[str, Any]:
        tx = self.send(ctx, request)
        rx_expect = request.get("expect") or {}
        if not isinstance(rx_expect, dict):
            rx_expect = {}
        rx = self.recv(ctx, rx_expect)
        out: Dict[str, Any] = {}
        out.update(tx)
        out.update(rx)
        return out
