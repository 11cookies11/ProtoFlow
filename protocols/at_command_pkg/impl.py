from __future__ import annotations

import re
from typing import Any, Dict, List


def _normalize_eol(name: str) -> str:
    key = str(name or "crlf").strip().lower()
    if key in {"crlf", "\\r\\n"}:
        return "\r\n"
    if key in {"cr", "\\r"}:
        return "\r"
    if key in {"lf", "\\n"}:
        return "\n"
    if key in {"none", ""}:
        return ""
    raise ValueError(f"AT_VALUE_INVALID: unsupported eol: {name}")


def _decode_lines(raw: bytes, encoding: str = "utf-8") -> List[str]:
    text = raw.decode(encoding, errors="ignore").replace("\r\n", "\n").replace("\r", "\n")
    return [line.strip() for line in text.split("\n") if line.strip()]


def _status_from_lines(lines: List[str]) -> str:
    for line in lines:
        upper = line.upper()
        if upper == "OK":
            return "ok"
        if upper == "ERROR" or upper.startswith("+CME ERROR") or upper.startswith("+CMS ERROR"):
            return "error"
    return "unknown"


def _assert_expect(lines: List[str], status: str, expect: Dict[str, Any]) -> None:
    if not expect:
        return
    if "status" in expect:
        required_status = str(expect.get("status")).strip().lower()
        if required_status and status != required_status:
            raise ValueError(f"AT_EXPECT_FAILED: status expected={required_status}, actual={status}")

    text = "\n".join(lines)
    contains = expect.get("contains")
    if contains is not None:
        token = str(contains)
        if token not in text:
            raise ValueError(f"AT_EXPECT_FAILED: contains not found: {token}")

    regex = expect.get("regex")
    if regex is not None:
        pattern = str(regex)
        if re.search(pattern, text) is None:
            raise ValueError(f"AT_EXPECT_FAILED: regex not matched: {pattern}")


class ProtocolPackage:
    def send(self, ctx, request: Dict[str, Any]) -> Dict[str, Any]:
        cmd = str(request.get("cmd", request.get("text", ""))).strip()
        if not cmd:
            raise ValueError("AT_VALUE_INVALID: request.cmd is required")
        eol = _normalize_eol(str(request.get("eol", "crlf")))
        payload = (cmd + eol).encode("utf-8")
        ctx.channel.write(payload)
        return {
            "ok": True,
            "cmd": cmd,
            "raw": {"tx_text": cmd + eol, "tx_hex": payload.hex().upper()},
            "size": len(payload),
        }

    def recv(self, ctx, expect: Dict[str, Any]) -> Dict[str, Any]:
        size = int(expect.get("size", 2048))
        raw = ctx.channel.read(size, timeout=max(0.01, ctx.timeout_ms / 1000.0))
        if not raw:
            raise TimeoutError("AT_TIMEOUT: no response bytes")
        lines = _decode_lines(raw, encoding=str(expect.get("encoding", "utf-8")))
        status = _status_from_lines(lines)
        _assert_expect(lines, status, expect)
        return {
            "ok": status != "error",
            "status": status,
            "lines": lines,
            "text": "\n".join(lines),
            "raw": {"rx_hex": raw.hex().upper()},
            "size": len(raw),
        }

    def rpc(self, ctx, request: Dict[str, Any]) -> Dict[str, Any]:
        tx = self.send(ctx, request)
        expect = dict(request.get("expect") or {})
        if "status" not in expect:
            expect["status"] = str(request.get("status", "ok"))
        rx = self.recv(ctx, expect)
        return {
            "ok": bool(rx.get("ok", False)),
            "status": rx.get("status"),
            "lines": rx.get("lines", []),
            "text": rx.get("text", ""),
            "raw": {"tx_hex": tx.get("raw", {}).get("tx_hex"), "rx_hex": rx.get("raw", {}).get("rx_hex")},
        }
