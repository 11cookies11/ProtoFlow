from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Protocol


@dataclass
class ProtocolCallContext:
    channel: Any
    logger: Any
    vars: Dict[str, Any]
    timeout_ms: int
    artifacts: Dict[str, Any]


class ProtocolPackageAPI(Protocol):
    def send(self, ctx: ProtocolCallContext, request: Dict[str, Any]) -> Dict[str, Any]:
        ...

    def recv(self, ctx: ProtocolCallContext, expect: Dict[str, Any]) -> Dict[str, Any]:
        ...

    def rpc(self, ctx: ProtocolCallContext, request: Dict[str, Any]) -> Dict[str, Any]:
        ...
