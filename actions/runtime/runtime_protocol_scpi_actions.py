from __future__ import annotations

from typing import Any, Dict

from actions.runtime.base import RuntimeTaskBase
from protocols.registry import ProtocolRegistry


class ScpiCommandTask(RuntimeTaskBase):
    def __init__(self) -> None:
        super().__init__(
            name="scpi_command",
            schema={
                "aliases": {"command": "cmd"},
                "required": ["channel", "cmd"],
                "optional": {"timeout": 2.0, "terminator": "\n", "expect_response": None, "strip": True},
                "types": {"timeout": "number", "strip": bool},
                "allow_extra": False,
            },
        )

    def execute(self, task: Dict[str, Any], channels: Dict[str, Any], logger) -> Any:
        channel_name = task.get("channel")
        if not channel_name or channel_name not in channels:
            raise KeyError(f"channel not found: {channel_name}")

        cmd = task.get("cmd")
        timeout = float(task.get("timeout", 2.0))
        terminator = task.get("terminator", "\n")
        expect_response = task.get("expect_response")
        strip = bool(task.get("strip", True))

        protocol_cls = ProtocolRegistry.get("scpi")
        protocol = protocol_cls(channels[channel_name], logger)
        return protocol.execute(
            cmd=str(cmd),
            expect_response=expect_response,
            timeout=timeout,
            terminator=terminator,
            strip=strip,
        )


_TASK = ScpiCommandTask()


def run(task: Dict[str, Any], channels: Dict[str, Any], logger) -> Any:
    return _TASK.run(task, channels, logger)
