from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

import yaml

from dsl_runtime.protocol_package.gateway import ProtocolPackageGateway
from dsl_runtime.protocol_package.loader import load_protocol_packages
from dsl_runtime.protocol_package.runtime import ProtocolCallContext


@dataclass
class VectorCaseResult:
    case_id: str
    kind: str
    ok: bool
    expected: Dict[str, Any]
    actual: Dict[str, Any]
    error: str = ""


@dataclass
class VectorRunResult:
    protocol_id: str
    package_dir: str
    cases: List[VectorCaseResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(c.ok for c in self.cases)


class _MockChannel:
    def __init__(self, *, rx_text: str = "", rx_hex: str = "") -> None:
        if rx_hex:
            self._rx = bytearray(bytes.fromhex(rx_hex.replace(" ", "")))
        else:
            self._rx = bytearray(rx_text.encode("utf-8"))
        self.tx = bytearray()

    def write(self, data: bytes | str) -> None:
        if isinstance(data, bytes):
            self.tx.extend(data)
            return
        self.tx.extend(str(data).encode("utf-8"))

    def read(self, size: int = 256, timeout: float | None = None) -> bytes:
        if not self._rx:
            return b""
        n = max(1, int(size))
        out = bytes(self._rx[:n])
        del self._rx[:n]
        return out

    def read_until(self, tail: bytes, timeout: float | None = None) -> bytes:
        if not self._rx:
            return b""
        idx = bytes(self._rx).find(tail)
        if idx < 0:
            out = bytes(self._rx)
            self._rx.clear()
            return out
        end = idx + len(tail)
        out = bytes(self._rx[:end])
        del self._rx[:end]
        return out


def _subset_match(expected: Any, actual: Any) -> bool:
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        for key, value in expected.items():
            if key not in actual:
                return False
            if not _subset_match(value, actual.get(key)):
                return False
        return True
    if isinstance(expected, list):
        if not isinstance(actual, list):
            return False
        if len(expected) > len(actual):
            return False
        for idx, value in enumerate(expected):
            if not _subset_match(value, actual[idx]):
                return False
        return True
    return expected == actual


def _assert_expected(expected: Dict[str, Any], actual: Dict[str, Any]) -> bool:
    return _subset_match(expected, actual)


def _load_vectors_file(path: Path) -> Dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("vectors.yaml root must be a mapping")
    return data


def run_protocol_vectors(root_dir: str | Path, protocol_id: str) -> VectorRunResult:
    load = load_protocol_packages(root_dir)
    if load.issues:
        errs = [x for x in load.issues if x.level == "error"]
        if errs and protocol_id not in load.packages:
            raise RuntimeError(f"protocol package load failed: {errs[0].message}")
    loaded = load.packages.get(protocol_id)
    if loaded is None:
        raise ValueError(f"protocol package not found: {protocol_id}")

    vectors_path = loaded.manifest.pkg_dir / "vectors.yaml"
    if not vectors_path.exists():
        raise FileNotFoundError(f"vectors.yaml not found: {vectors_path}")
    vec = _load_vectors_file(vectors_path)
    cases = vec.get("cases")
    if not isinstance(cases, list):
        raise ValueError("vectors.yaml cases must be a list")

    gateway = ProtocolPackageGateway({protocol_id: loaded})
    run = VectorRunResult(protocol_id=protocol_id, package_dir=str(loaded.manifest.pkg_dir))
    for idx, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(f"cases[{idx}] must be a mapping")
        case_id = str(case.get("id") or f"case_{idx + 1}")
        kind = str(case.get("kind") or "").strip().lower()
        if kind not in {"send", "recv", "rpc"}:
            raise ValueError(f"cases[{idx}].kind must be send/recv/rpc")
        input_data = case.get("input") or {}
        if not isinstance(input_data, dict):
            raise ValueError(f"cases[{idx}].input must be a mapping")
        expected = case.get("expect") or {}
        if not isinstance(expected, dict):
            raise ValueError(f"cases[{idx}].expect must be a mapping")

        channel = _MockChannel(
            rx_text=str(input_data.get("mock_rx_text", "")),
            rx_hex=str(input_data.get("mock_rx_hex", "")),
        )
        call_ctx = ProtocolCallContext(
            channel=channel,
            logger=None,
            vars={},
            timeout_ms=int(input_data.get("timeout_ms", 1000)),
            artifacts={},
        )
        if kind == "recv":
            payload = input_data.get("expect", {})
        else:
            payload = input_data.get("request", {})
        if payload is None:
            payload = {}
        if not isinstance(payload, dict):
            raise ValueError(f"cases[{idx}] payload must be a mapping")

        call = gateway.call(protocol_id=protocol_id, method=kind, ctx=call_ctx, payload=payload)
        actual = {
            "ok": call.ok,
            "error": call.error,
            "data": call.data,
            "tx_hex": bytes(channel.tx).hex().upper(),
        }
        passed = _assert_expected(expected, actual)
        err_text = ""
        if not passed:
            err_text = "expected values not matched"
        run.cases.append(
            VectorCaseResult(
                case_id=case_id,
                kind=kind,
                ok=passed,
                expected=expected,
                actual=actual,
                error=err_text,
            )
        )
    return run
