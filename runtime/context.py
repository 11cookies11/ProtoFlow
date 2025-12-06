from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from actions.registry import ActionRegistry
from dsl.expression import eval_expr


class RuntimeContext:
    def __init__(self, channels: Dict[str, Any], default_channel: str, vars_init: Dict[str, Any]) -> None:
        self.channels = channels
        self.channel = channels[default_channel]
        self.vars: Dict[str, Any] = dict(vars_init)
        self.logger = logging.getLogger("dsl")
        self._last_event: Optional[str] = None

    def set_var(self, key: str, value: Any) -> None:
        self.vars[key] = value

    def vars_snapshot(self) -> Dict[str, Any]:
        snap = dict(self.vars)
        snap["event"] = self._last_event
        return snap

    def eval_value(self, value: Any) -> Any:
        if isinstance(value, str) and "$" in value:
            return eval_expr(value, self.vars_snapshot())
        return value

    def run_action(self, name: str, args: Dict[str, Any]) -> Any:
        fn = ActionRegistry.get(name)
        return fn(self, args or {})

    def next_event(self, timeout: float = 0.1) -> Optional[str]:
        evt = self.channel.read_event(timeout=timeout)
        if evt is not None:
            self._last_event = evt
        return evt

    def channel_write(self, data: bytes | str) -> None:
        self.channel.write(data)
