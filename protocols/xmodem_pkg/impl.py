from __future__ import annotations

from typing import Any, Dict


SOH = 0x01
EOT = 0x04
ACK = 0x06
NAK = 0x15


def _checksum(payload: bytes) -> int:
    return sum(payload) & 0xFF


def _build_block(seq: int, data: bytes) -> bytes:
    if len(data) > 128:
        raise ValueError("xmodem block data too large")
    if len(data) < 128:
        data = data + bytes([0x1A]) * (128 - len(data))
    seq_b = seq & 0xFF
    return bytes([SOH, seq_b, 0xFF - seq_b]) + data + bytes([_checksum(data)])


class ProtocolPackage:
    def send(self, ctx, request: Dict[str, Any]) -> Dict[str, Any]:
        kind = str(request.get("kind", "block")).strip().lower()
        if kind == "eot":
            frame = bytes([EOT])
            ctx.channel.write(frame)
            return {"tx_hex": frame.hex().upper(), "kind": "eot"}

        seq = int(request.get("seq", 1))
        data_hex = str(request.get("data_hex", "")).strip()
        data = bytes.fromhex(data_hex.replace(" ", ""))
        frame = _build_block(seq, data)
        ctx.channel.write(frame)
        return {"tx_hex": frame.hex().upper(), "kind": "block", "seq": seq}

    def recv(self, ctx, expect: Dict[str, Any]) -> Dict[str, Any]:
        size = int(expect.get("size", 1))
        rx = ctx.channel.read(size, timeout=max(0.01, ctx.timeout_ms / 1000.0))
        if not rx:
            raise TimeoutError("xmodem recv timeout")
        return {"rx_hex": rx.hex().upper(), "ack": (rx[0] == ACK)}

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
