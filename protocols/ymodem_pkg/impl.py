from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple


SOH = 0x01
STX = 0x02
EOT = 0x04
ACK = 0x06
NAK = 0x15
CAN = 0x18
CRC_REQ = 0x43  # 'C'


def _crc16_xmodem(data: bytes) -> int:
    crc = 0
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc & 0xFFFF


def _split_blocks(data: bytes, block_size: int) -> List[bytes]:
    if block_size not in {128, 1024}:
        raise ValueError("YMODEM_VALUE_INVALID: block_size must be 128 or 1024")
    out: List[bytes] = []
    for i in range(0, len(data), block_size):
        chunk = data[i : i + block_size]
        if len(chunk) < block_size:
            chunk = chunk + bytes([0x1A]) * (block_size - len(chunk))
        out.append(chunk)
    if not out:
        out.append(bytes([0x1A]) * block_size)
    return out


def _make_packet(seq: int, payload: bytes) -> bytes:
    size = len(payload)
    if size == 128:
        head = SOH
    elif size == 1024:
        head = STX
    else:
        raise ValueError("YMODEM_VALUE_INVALID: payload size must be 128 or 1024")
    seq_b = seq & 0xFF
    crc = _crc16_xmodem(payload)
    return bytes([head, seq_b, 0xFF - seq_b]) + payload + bytes([(crc >> 8) & 0xFF, crc & 0xFF])


def _make_header_packet(filename: str, total_size: int) -> bytes:
    if not filename:
        filename = "firmware.bin"
    meta = f"{filename}\0{total_size}\0".encode("ascii", errors="ignore")
    payload = meta[:128].ljust(128, b"\x00")
    return _make_packet(0, payload)


def _make_end_packet() -> bytes:
    return _make_packet(0, bytes(128))


def _wait_symbol(ctx, allowed: Tuple[int, ...], timeout_ms: int) -> int:
    remaining = int(timeout_ms)
    while remaining > 0:
        timeout_s = min(0.1, max(0.01, remaining / 1000.0))
        raw = ctx.channel.read(1, timeout=timeout_s)
        if raw:
            sym = int(raw[0])
            if sym == CAN:
                raise RuntimeError("YMODEM_CANCELED: transfer canceled by receiver")
            if sym in allowed:
                return sym
        remaining -= int(timeout_s * 1000)
    raise TimeoutError(f"YMODEM_TIMEOUT: wait symbol {allowed}")


def _send_with_retry(ctx, packet: bytes, *, max_retry: int, timeout_ms: int) -> int:
    retry_count = 0
    for _ in range(max_retry + 1):
        ctx.channel.write(packet)
        sym = _wait_symbol(ctx, (ACK, NAK, CAN), timeout_ms)
        if sym == ACK:
            return retry_count
        if sym == NAK:
            retry_count += 1
            continue
    raise RuntimeError("YMODEM_RETRY_EXCEEDED: packet was not ACKed")


def _load_transfer_data(request: Dict[str, Any]) -> Tuple[str, bytes]:
    if "data_hex" in request and request.get("data_hex") is not None:
        data_hex = str(request.get("data_hex")).strip()
        data = bytes.fromhex(data_hex.replace(" ", ""))
        filename = str(request.get("filename", "firmware.bin"))
        return filename, data

    file_path = str(request.get("file_path", "")).strip()
    if not file_path:
        raise ValueError("YMODEM_VALUE_INVALID: file_path or data_hex is required")
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"YMODEM_FILE_NOT_FOUND: {file_path}")
    filename = str(request.get("filename", p.name))
    return filename, p.read_bytes()


def _symbol_name(sym: int) -> str:
    if sym == ACK:
        return "ACK"
    if sym == NAK:
        return "NAK"
    if sym == CAN:
        return "CAN"
    if sym == CRC_REQ:
        return "C"
    if sym == EOT:
        return "EOT"
    return f"0x{sym:02X}"


class ProtocolPackage:
    def send(self, ctx, request: Dict[str, Any]) -> Dict[str, Any]:
        op = str(request.get("op", "send_data")).strip().lower()
        if op not in {"send_data", "send_file"}:
            raise ValueError(f"YMODEM_VALUE_INVALID: unsupported op: {op}")

        timeout_ms = int(request.get("timeout_ms", ctx.timeout_ms))
        max_retry = int(request.get("max_retry", 10))
        block_size = int(request.get("block_size", 1024))
        if max_retry < 0:
            raise ValueError("YMODEM_VALUE_INVALID: max_retry must be >= 0")

        filename, data = _load_transfer_data(request)
        blocks = _split_blocks(data, block_size)
        retries = 0

        _wait_symbol(ctx, (CRC_REQ,), timeout_ms)
        header = _make_header_packet(filename, len(data))
        retries += _send_with_retry(ctx, header, max_retry=max_retry, timeout_ms=timeout_ms)
        _wait_symbol(ctx, (CRC_REQ,), timeout_ms)

        seq = 1
        for block in blocks:
            pkt = _make_packet(seq, block)
            retries += _send_with_retry(ctx, pkt, max_retry=max_retry, timeout_ms=timeout_ms)
            seq = (seq + 1) & 0xFF

        ctx.channel.write(bytes([EOT]))
        _wait_symbol(ctx, (ACK,), timeout_ms)
        _wait_symbol(ctx, (CRC_REQ,), timeout_ms)

        end_pkt = _make_end_packet()
        retries += _send_with_retry(ctx, end_pkt, max_retry=max_retry, timeout_ms=timeout_ms)

        return {
            "ok": True,
            "status": "done",
            "filename": filename,
            "bytes_total": len(data),
            "blocks_total": len(blocks),
            "retries": retries,
            "block_size": block_size,
        }

    def recv(self, ctx, expect: Dict[str, Any]) -> Dict[str, Any]:
        timeout_ms = int(expect.get("timeout_ms", ctx.timeout_ms))
        allowed_names = expect.get("allowed", ["ACK", "NAK", "C", "CAN", "EOT"])
        if not isinstance(allowed_names, list) or not allowed_names:
            raise ValueError("YMODEM_VALUE_INVALID: expect.allowed must be non-empty list")
        map_name = {"ACK": ACK, "NAK": NAK, "C": CRC_REQ, "CAN": CAN, "EOT": EOT}
        allowed = []
        for name in allowed_names:
            key = str(name).strip().upper()
            if key not in map_name:
                raise ValueError(f"YMODEM_VALUE_INVALID: unsupported symbol: {name}")
            allowed.append(map_name[key])
        sym = _wait_symbol(ctx, tuple(allowed), timeout_ms)
        return {"ok": True, "symbol": _symbol_name(sym), "byte": sym}

    def rpc(self, ctx, request: Dict[str, Any]) -> Dict[str, Any]:
        op = str(request.get("op", "send_data")).strip().lower()
        if op in {"send_data", "send_file"}:
            return self.send(ctx, request)

        send_req = request.get("send") or {}
        recv_req = request.get("expect") or {}
        if not isinstance(send_req, dict):
            raise ValueError("YMODEM_VALUE_INVALID: request.send must be mapping")
        if not isinstance(recv_req, dict):
            raise ValueError("YMODEM_VALUE_INVALID: request.expect must be mapping")
        tx = self.send(ctx, send_req)
        rx = self.recv(ctx, recv_req)
        out: Dict[str, Any] = {"ok": True}
        out.update(tx)
        out["recv"] = rx
        return out
