from __future__ import annotations

from typing import Any, Dict

from actions.runtime.base import RuntimeTaskBase
from protocols.registry import ProtocolRegistry


class AtCommandTask(RuntimeTaskBase):
    def __init__(self) -> None:
        super().__init__(
            name="at_command",
            schema={
                "aliases": {"command": "cmd"},
                "required": ["channel", "cmd"],
                "optional": {"timeout": 2.0, "terminator": "\r\n", "ok": "OK", "error": "ERROR", "echo": True},
                "types": {"timeout": "number", "echo": bool},
                "allow_extra": False,
            },
        )

    def execute(self, task: Dict[str, Any], channels: Dict[str, Any], logger) -> Any:
        channel_name = task.get("channel")
        if not channel_name or channel_name not in channels:
            raise KeyError(f"channel not found: {channel_name}")

        cmd = task.get("cmd")
        timeout = float(task.get("timeout", 2.0))
        terminator = task.get("terminator", "\r\n")
        ok = str(task.get("ok", "OK"))
        error = str(task.get("error", "ERROR"))
        echo = bool(task.get("echo", True))

        protocol_cls = ProtocolRegistry.get("at")
        protocol = protocol_cls(channels[channel_name], logger)
        return protocol.execute(cmd=str(cmd), timeout=timeout, terminator=terminator, ok=ok, error=error, echo=echo)


_TASK = AtCommandTask()


def run(task: Dict[str, Any], channels: Dict[str, Any], logger) -> Any:
    return _TASK.run(task, channels, logger)
