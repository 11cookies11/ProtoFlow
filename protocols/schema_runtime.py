from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from utils.crc16 import crc16_modbus
from utils.path_utils import resolve_resource_path


def _hex_to_bytes(value: str | bytes | None) -> bytes:
    if value is None:
        return b""
    if isinstance(value, (bytes, bytearray)):
        return bytes(value)
    txt = str(value).replace(" ", "").replace("0x", "")
    if txt == "":
        return b""
    if len(txt) % 2 != 0:
        txt = "0" + txt
    return bytes.fromhex(txt)


def _pack_int(val: int, bits: int, endian: str = "big") -> bytes:
    size = bits // 8
    return int(val).to_bytes(size, endian)


def _unpack_int(data: bytes, endian: str = "big") -> int:
    return int.from_bytes(data, endian)


@dataclass
class FieldDef:
    name: Optional[str]
    ftype: str
    const: Any = None
    length: Optional[int] = None
    endian: str = "big"
    encoding: str = "ascii"


@dataclass
class FrameDef:
    name: str
    header: bytes
    tail: bytes
    crc: Optional[str]
    fields: List[FieldDef]

    @property
    def crc_size(self) -> int:
        if self.crc == "crc16_modbus":
            return 2
        if self.crc == "crc8":
            return 1
        return 0

    def fixed_length(self) -> Optional[int]:
        total = len(self.header) + len(self.tail) + self.crc_size
        for fld in self.fields:
            if fld.ftype in {"u8", "u16", "u32"}:
                total += {"u8": 1, "u16": 2, "u32": 4}[fld.ftype]
            elif fld.ftype in {"bytes", "str"}:
                if fld.length is None:
                    return None
                total += fld.length
            else:
                return None
        return total


class ProtocolSchema:
    def __init__(self, frames: Dict[str, FrameDef]) -> None:
        self.frames = frames

    @classmethod
    def load(cls, path: str | Path) -> "ProtocolSchema":
        resolved = resolve_resource_path(path)
        if not resolved.exists():
            raise FileNotFoundError(f"Schema not found: {resolved}")
        with resolved.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        frames_cfg = data.get("frames") or {}
        frames: Dict[str, FrameDef] = {}
        for name, cfg in frames_cfg.items():
            fields_cfg = cfg.get("fields") or []
            fields: List[FieldDef] = []
            for item in fields_cfg:
                if not isinstance(item, dict):
                    raise ValueError(f"Invalid field in frame {name}: {item}")
                fields.append(
                    FieldDef(
                        name=item.get("name"),
                        ftype=str(item.get("type", "bytes")).lower(),
                        const=item.get("const"),
                        length=int(item["length"]) if "length" in item else None,
                        endian=str(item.get("endian", "big")),
                        encoding=str(item.get("encoding", "ascii")),
                    )
                )
            frames[name] = FrameDef(
                name=name,
                header=_hex_to_bytes(cfg.get("header")),
                tail=_hex_to_bytes(cfg.get("tail")),
                crc=cfg.get("crc"),
                fields=fields,
            )
        if not frames:
            raise ValueError(f"No frames defined in schema: {resolved}")
        return cls(frames)

    def build(self, frame: str, values: Dict[str, Any]) -> bytes:
        if frame not in self.frames:
            raise KeyError(f"Unknown frame: {frame}")
        fd = self.frames[frame]
        body = bytearray()
        for fld in fd.fields:
            val = values.get(fld.name) if fld.name else None
            if fld.const is not None:
                val = fld.const
            if fld.ftype == "u8":
                body.extend(_pack_int(int(val), 8, fld.endian))
            elif fld.ftype == "u16":
                body.extend(_pack_int(int(val), 16, fld.endian))
            elif fld.ftype == "u32":
                body.extend(_pack_int(int(val), 32, fld.endian))
            elif fld.ftype == "str":
                raw = str(val).encode(fld.encoding)
                if fld.length is not None:
                    raw = raw[: fld.length].ljust(fld.length, b"\x00")
                body.extend(raw)
            elif fld.ftype == "bytes":
                raw_bytes = (
                    val if isinstance(val, (bytes, bytearray)) else bytes.fromhex(str(val)) if isinstance(val, str) else b""
                )
                if fld.length is not None:
                    raw_bytes = raw_bytes[: fld.length].ljust(fld.length, b"\x00")
                body.extend(raw_bytes)
            else:
                raise ValueError(f"Unsupported field type: {fld.ftype}")

        crc_bytes = self._calc_crc(fd, bytes(body))
        return fd.header + bytes(body) + crc_bytes + fd.tail

    def parse(self, frame: str, data: bytes) -> Dict[str, Any]:
        if frame not in self.frames:
            raise KeyError(f"Unknown frame: {frame}")
        fd = self.frames[frame]
        buf = data
        if fd.header and not buf.startswith(fd.header):
            raise ValueError("Header mismatch")
        if fd.header:
            buf = buf[len(fd.header) :]
        if fd.tail and not buf.endswith(fd.tail):
            raise ValueError("Tail mismatch")
        if fd.tail:
            buf = buf[: -len(fd.tail)]
        if len(buf) < fd.crc_size:
            raise ValueError("Frame too short")
        payload, crc_part = buf[: len(buf) - fd.crc_size], buf[len(buf) - fd.crc_size :]
        if fd.crc and not self._verify_crc(fd, payload, crc_part):
            raise ValueError("CRC check failed")

        pos = 0
        result: Dict[str, Any] = {}
        for fld in fd.fields:
            if fld.ftype == "u8":
                chunk = payload[pos : pos + 1]
                pos += 1
                val = _unpack_int(chunk, fld.endian)
            elif fld.ftype == "u16":
                chunk = payload[pos : pos + 2]
                pos += 2
                val = _unpack_int(chunk, fld.endian)
            elif fld.ftype == "u32":
                chunk = payload[pos : pos + 4]
                pos += 4
                val = _unpack_int(chunk, fld.endian)
            elif fld.ftype in {"bytes", "str"}:
                if fld.length is not None:
                    chunk = payload[pos : pos + fld.length]
                    pos += fld.length
                else:
                    chunk = payload[pos:]
                    pos = len(payload)
                if fld.ftype == "str":
                    val = chunk.decode(fld.encoding, errors="ignore").rstrip("\x00")
                else:
                    val = chunk
            else:
                raise ValueError(f"Unsupported field type: {fld.ftype}")

            if fld.const is not None and str(val) != str(fld.const):
                raise ValueError(f"Const mismatch on {fld.name}: {val} != {fld.const}")
            if fld.name:
                result[fld.name] = val

        return result

    def _calc_crc(self, fd: FrameDef, payload: bytes) -> bytes:
        if fd.crc == "crc16_modbus":
            return crc16_modbus(payload).to_bytes(2, "little")
        if fd.crc == "crc8":
            return bytes([self._crc8(payload)])
        return b""

    def _verify_crc(self, fd: FrameDef, payload: bytes, crc_part: bytes) -> bool:
        if fd.crc == "crc16_modbus":
            return crc_part == crc16_modbus(payload).to_bytes(2, "little")
        if fd.crc == "crc8":
            return crc_part == bytes([self._crc8(payload)])
        return True

    @staticmethod
    def _crc8(data: bytes, poly: int = 0x07, init: int = 0x00) -> int:
        crc = init
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = ((crc << 1) ^ poly) & 0xFF
                else:
                    crc = (crc << 1) & 0xFF
        return crc & 0xFF

    def dump(self) -> str:
        return json.dumps(
            {
                "frames": {
                    name: {
                        "header": fd.header.hex(),
                        "tail": fd.tail.hex(),
                        "crc": fd.crc,
                        "fields": [vars(f) for f in fd.fields],
                    }
                    for name, fd in self.frames.items()
                }
            },
            indent=2,
        )
