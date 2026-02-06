from __future__ import annotations

from typing import Any, Dict

from actions.runtime.base import RuntimeTaskBase
from protocols.registry import ProtocolRegistry


class XmodemSendTask(RuntimeTaskBase):
    def __init__(self) -> None:
        super().__init__(
            name="xmodem_send",
            schema={
                "aliases": {"path": "file"},
                "required": ["channel", "file"],
                "optional": {"retries": 10, "start_timeout": 10.0},
                "types": {"retries": "number", "start_timeout": "number"},
                "allow_extra": False,
            },
        )

    def execute(self, task: Dict[str, Any], channels: Dict[str, Any], logger) -> Any:
        channel_name = task.get("channel")
        if not channel_name or channel_name not in channels:
            raise KeyError(f"未找到通道: {channel_name}")
        file_path = task.get("file")
        if not file_path:
            raise ValueError("xmodem_send 需要 file/path 参数")

        retries = int(task.get("retries", 10))
        start_timeout = float(task.get("start_timeout", 10.0))

        protocol_cls = ProtocolRegistry.get("xmodem")
        protocol = protocol_cls(channels[channel_name], logger)
        return protocol.execute(file_path=file_path, retries=retries, start_timeout=start_timeout)


_TASK = XmodemSendTask()


def run(task: Dict[str, Any], channels: Dict[str, Any], logger) -> Any:
    return _TASK.run(task, channels, logger)
