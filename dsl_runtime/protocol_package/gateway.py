from __future__ import annotations

from dataclasses import dataclass
import time
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

    @staticmethod
    def _audit(ctx: ProtocolCallContext, payload: Dict[str, Any]) -> None:
        logger = getattr(ctx, "logger", None)
        if logger is None:
            return
        log_fn = getattr(logger, "info", None)
        if callable(log_fn):
            log_fn(f"[protocol.gateway] {payload}")

    @staticmethod
    def _error(code: str, message: str) -> ProtocolCallResult:
        return ProtocolCallResult(ok=False, data={}, error={"code": code, "message": message})

    @staticmethod
    def _map_exception(exc: Exception) -> str:
        if isinstance(exc, TimeoutError):
            return "PROTOCOL_TIMEOUT"
        if isinstance(exc, ValueError):
            return "PROTOCOL_VALIDATION_FAILED"
        if isinstance(exc, PermissionError):
            return "PROTOCOL_PERMISSION_DENIED"
        return "PROTOCOL_CALL_FAILED"

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
        started = time.time()
        self._audit(
            ctx,
            {
                "event": "call_start",
                "protocol_id": protocol_id,
                "method": method,
            },
        )
        pkg = self._packages.get(protocol_id)
        if pkg is None:
            result = self._error("PROTOCOL_NOT_FOUND", f"protocol package not found: {protocol_id}")
            self._audit(ctx, {"event": "call_end", "ok": False, "error": result.error, "elapsed_ms": 0})
            return result
        method_name = str(method).strip().lower()
        if method_name not in {"send", "recv", "rpc"}:
            result = self._error("PROTOCOL_METHOD_INVALID", f"invalid protocol method: {method_name}")
            self._audit(ctx, {"event": "call_end", "ok": False, "error": result.error, "elapsed_ms": 0})
            return result
        if method_name not in set(pkg.manifest.api):
            result = self._error("PROTOCOL_METHOD_UNDECLARED", f"method not declared by package: {method_name}")
            self._audit(ctx, {"event": "call_end", "ok": False, "error": result.error, "elapsed_ms": 0})
            return result
        fn = getattr(pkg.impl, method_name, None)
        if fn is None or not callable(fn):
            result = self._error("PROTOCOL_METHOD_UNSUPPORTED", f"method not implemented: {method_name}")
            self._audit(ctx, {"event": "call_end", "ok": False, "error": result.error, "elapsed_ms": 0})
            return result
        try:
            result = fn(ctx, payload)
            if isinstance(result, dict):
                output = ProtocolCallResult(ok=True, data=result)
            else:
                output = ProtocolCallResult(ok=True, data={"result": result})
            self._audit(
                ctx,
                {
                    "event": "call_end",
                    "ok": True,
                    "protocol_id": protocol_id,
                    "method": method_name,
                    "elapsed_ms": int((time.time() - started) * 1000),
                },
            )
            return output
        except Exception as exc:
            err = {"code": self._map_exception(exc), "message": str(exc)}
            self._audit(
                ctx,
                {
                    "event": "call_end",
                    "ok": False,
                    "protocol_id": protocol_id,
                    "method": method_name,
                    "error": err,
                    "elapsed_ms": int((time.time() - started) * 1000),
                },
            )
            return ProtocolCallResult(ok=False, data={}, error=err)
