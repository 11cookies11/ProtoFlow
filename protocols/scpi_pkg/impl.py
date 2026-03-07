from __future__ import annotations

import re
from typing import Any, Dict, List


_NUM_UNIT_RE = re.compile(r"^\s*([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*([A-Za-z%]+)?\s*$")
_SCPI_ERR_RE = re.compile(r"^\s*-\d+\s*,")


def _normalize_eol(name: str) -> str:
    key = str(name or "lf").strip().lower()
    if key in {"lf", "\\n"}:
        return "\n"
    if key in {"crlf", "\\r\\n"}:
        return "\r\n"
    if key in {"cr", "\\r"}:
        return "\r"
    if key in {"none", ""}:
        return ""
    raise ValueError(f"SCPI_VALUE_INVALID: unsupported eol: {name}")


def _decode_text(raw: bytes, encoding: str = "utf-8") -> str:
    return raw.decode(encoding, errors="ignore")


def _split_lines(text: str) -> List[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return [line.strip() for line in normalized.split("\n") if line.strip()]


def _parse_scalar(token: str) -> Dict[str, Any]:
    m = _NUM_UNIT_RE.match(token)
    if m is None:
        return {"raw": token}
    num_text = str(m.group(1))
    unit = str(m.group(2) or "")
    if "." in num_text or "e" in num_text.lower():
        value: Any = float(num_text)
    else:
        value = int(num_text)
    return {"value": value, "unit": unit, "raw": token}


def _parse_csv(line: str) -> List[Dict[str, Any]]:
    parts = [part.strip() for part in line.split(",")]
    return [_parse_scalar(part) for part in parts]


def _assert_expect(text: str, lines: List[str], status: str, expect: Dict[str, Any]) -> None:
    if not expect:
        return
    if "status" in expect:
        required = str(expect.get("status")).strip().lower()
        if required and status != required:
            raise ValueError(f"SCPI_EXPECT_FAILED: status expected={required}, actual={status}")
    if "contains" in expect:
        token = str(expect.get("contains"))
        if token not in text:
            raise ValueError(f"SCPI_EXPECT_FAILED: contains not found: {token}")
    if "regex" in expect:
        pattern = str(expect.get("regex"))
        if re.search(pattern, text) is None:
            raise ValueError(f"SCPI_EXPECT_FAILED: regex not matched: {pattern}")
    if "min_lines" in expect:
        min_lines = int(expect.get("min_lines"))
        if len(lines) < min_lines:
            raise ValueError(f"SCPI_EXPECT_FAILED: line count too small: {len(lines)} < {min_lines}")


class ProtocolPackage:
    def send(self, ctx, request: Dict[str, Any]) -> Dict[str, Any]:
        cmd = str(request.get("cmd", request.get("command", ""))).strip()
        if not cmd:
            raise ValueError("SCPI_VALUE_INVALID: request.cmd is required")
        eol = _normalize_eol(str(request.get("eol", "lf")))
        payload = (cmd + eol).encode("utf-8")
        ctx.channel.write(payload)
        return {"ok": True, "cmd": cmd, "raw": {"tx_text": cmd + eol, "tx_hex": payload.hex().upper()}, "size": len(payload)}

    def recv(self, ctx, expect: Dict[str, Any]) -> Dict[str, Any]:
        size = int(expect.get("size", 4096))
        raw = ctx.channel.read(size, timeout=max(0.01, ctx.timeout_ms / 1000.0))
        if not raw:
            raise TimeoutError("SCPI_TIMEOUT: no response bytes")
        text = _decode_text(raw, encoding=str(expect.get("encoding", "utf-8")))
        lines = _split_lines(text)
        status = "error" if any(_SCPI_ERR_RE.match(line) for line in lines) else "ok"
        _assert_expect(text, lines, status, expect)

        first_line = lines[0] if lines else ""
        csv_parsed = _parse_csv(first_line) if first_line else []
        return {
            "ok": status == "ok",
            "status": status,
            "lines": lines,
            "text": "\n".join(lines),
            "csv": csv_parsed,
            "raw": {"rx_hex": raw.hex().upper()},
            "size": len(raw),
        }

    def rpc(self, ctx, request: Dict[str, Any]) -> Dict[str, Any]:
        tx = self.send(ctx, request)
        cmd = str(request.get("cmd", request.get("command", ""))).strip()
        expect = dict(request.get("expect") or {})
        skip_recv = bool(request.get("skip_recv", ("?" not in cmd and not expect)))
        if skip_recv:
            return {"ok": True, "status": "sent", "cmd": cmd, "raw": {"tx_hex": tx.get("raw", {}).get("tx_hex")}}
        rx = self.recv(ctx, expect)
        out: Dict[str, Any] = {"ok": bool(rx.get("ok", False))}
        out.update(rx)
        out["raw"] = {"tx_hex": tx.get("raw", {}).get("tx_hex"), "rx_hex": rx.get("raw", {}).get("rx_hex")}
        return out
