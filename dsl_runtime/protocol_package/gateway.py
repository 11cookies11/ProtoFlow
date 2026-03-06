from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from dsl_runtime.protocol_package.loader import LoadedProtocolPackage
from dsl_runtime.protocol_package.runtime import ProtocolCallContext


@dataclass
class ProtocolCallResult:
    ok: bool
    data: Dict[str, Any]
    error: Dict[str, Any] | None = None


class ProtocolPackageGateway:
    def __init__(self, packages: Dict[str, LoadedProtocolPackage]) -> None:
        self._packages = packages

    def list_protocols(self) -> Dict[str, Dict[str, Any]]:
        return {
            pid: {
                "id": pid,
                "name": p.manifest.name,
                "version": p.manifest.version,
                "api": list(p.manifest.api),
            }
            for pid, p in self._packages.items()
        }

    def call(self, protocol_id: str, method: str, ctx: ProtocolCallContext, payload: Dict[str, Any]) -> ProtocolCallResult:
        pkg = self._packages.get(protocol_id)
        if pkg is None:
            return ProtocolCallResult(
                ok=False,
                data={},
                error={"code": "PROTOCOL_NOT_FOUND", "message": f"protocol package not found: {protocol_id}"},
            )
        method_name = str(method).strip().lower()
        if method_name not in {"send", "recv", "rpc"}:
            return ProtocolCallResult(
                ok=False,
                data={},
                error={"code": "PROTOCOL_METHOD_INVALID", "message": f"invalid protocol method: {method_name}"},
            )
        if method_name not in set(pkg.manifest.api):
            return ProtocolCallResult(
                ok=False,
                data={},
                error={"code": "PROTOCOL_METHOD_UNDECLARED", "message": f"method not declared by package: {method_name}"},
            )
        fn = getattr(pkg.impl, method_name, None)
        if fn is None or not callable(fn):
            return ProtocolCallResult(
                ok=False,
                data={},
                error={"code": "PROTOCOL_METHOD_UNSUPPORTED", "message": f"method not implemented: {method_name}"},
            )
        try:
            result = fn(ctx, payload)
            if isinstance(result, dict):
                return ProtocolCallResult(ok=True, data=result)
            return ProtocolCallResult(ok=True, data={"result": result})
        except Exception as exc:
            return ProtocolCallResult(
                ok=False,
                data={},
                error={"code": "PROTOCOL_CALL_FAILED", "message": str(exc)},
            )
