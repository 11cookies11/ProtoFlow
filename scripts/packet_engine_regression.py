from __future__ import annotations

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.packet_engine import PacketAnalysisEngine
from infra.common.event_bus import EventBus
from infra.protocol.protocol_loader import crc16_modbus


def _build_modbus_frame(body: bytes) -> bytes:
    crc = crc16_modbus(body)
    return body + crc.to_bytes(2, "little")


def main() -> int:
    bus = EventBus()
    EventBus._log = staticmethod(lambda _m: None)  # type: ignore[method-assign]
    engine = PacketAnalysisEngine(bus)

    checks: list[tuple[str, bool]] = []

    valid = _build_modbus_frame(bytes.fromhex("01 03 00 00 00 02"))
    p_name, p_unknown, _summary, _tree, errors = engine._parse_protocol(valid)
    checks.append(("valid.modbus_name", p_name == "Modbus RTU"))
    checks.append(("valid.not_unknown", p_unknown is False))
    checks.append(("valid.no_errors", len(errors) == 0))

    bad_crc = valid[:-1] + bytes([valid[-1] ^ 0xFF])
    p_name, p_unknown, _summary, _tree, errors = engine._parse_protocol(bad_crc)
    has_crc_error = any(e.get("code") == "CRC_INVALID" for e in errors)
    checks.append(("bad_crc.modbus_name", p_name == "Modbus RTU"))
    checks.append(("bad_crc.not_unknown", p_unknown is False))
    checks.append(("bad_crc.has_crc_error", has_crc_error))

    too_short = bytes.fromhex("01 03 00")
    p_name, p_unknown, _summary, _tree, errors = engine._parse_protocol(too_short)
    has_short_error = any(e.get("code") == "FRAME_TOO_SHORT" for e in errors)
    checks.append(("short.modbus_name", p_name == "Modbus RTU"))
    checks.append(("short.not_unknown", p_unknown is False))
    checks.append(("short.has_short_error", has_short_error))

    exc_invalid_len = _build_modbus_frame(bytes.fromhex("01 83 02 01"))
    p_name, p_unknown, _summary, _tree, errors = engine._parse_protocol(exc_invalid_len)
    has_len_error = any(e.get("code") == "LENGTH_INVALID" for e in errors)
    checks.append(("exception_len.modbus_name", p_name == "Modbus RTU"))
    checks.append(("exception_len.not_unknown", p_unknown is False))
    checks.append(("exception_len.has_len_error", has_len_error))

    ok = True
    for name, passed in checks:
        print(f"[{'PASS' if passed else 'FAIL'}] {name}")
        ok = ok and passed
    print(f"RESULT: {'PASSED' if ok else 'FAILED'}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
