from __future__ import annotations

import logging
import queue
from typing import Any, Dict, Optional

from actions.registry import ActionRegistry
from dsl.expression import eval_expr


class RuntimeContext:
    def __init__(
        self,
        channels: Dict[str, Any],
        default_channel: str,
        vars_init: Dict[str, Any],
        bus=None,
        external_events: Optional[list[str]] = None,
    ) -> None:
        self.channels = channels
        self.channel = channels[default_channel]
        self.vars: Dict[str, Any] = dict(vars_init)
        self.logger = logging.getLogger("dsl")
        self._last_event: Any = None
        self._last_event_name: Optional[str] = None
        self._last_event_payload: Any = None
        self._bus = bus
        self._bus_handlers: list[tuple[str, Any]] = []
        self._event_queue: "queue.SimpleQueue[tuple[str, Any]]" = queue.SimpleQueue()
        if self._bus and external_events:
            for name in external_events:
                handler = self._make_bus_handler(name)
                self._bus.subscribe(name, handler)
                self._bus_handlers.append((name, handler))

    def set_var(self, key: str, value: Any) -> None:
        self.vars[key] = value

    def vars_snapshot(self) -> Dict[str, Any]:
        snap = dict(self.vars)
        snap["event"] = self._last_event
        snap["event_name"] = self._last_event_name
        snap["event_payload"] = self._last_event_payload
        return snap

    def eval_value(self, value: Any) -> Any:
        if isinstance(value, str) and "$" in value:
            return eval_expr(value, self.vars_snapshot())
        return value

    def run_action(self, name: str, args: Dict[str, Any]) -> Any:
        fn = ActionRegistry.get(name)
        return fn(self, args or {})

    def next_event(self, timeout: float = 0.1) -> Optional[str]:
        try:
            name, payload = self._event_queue.get_nowait()
            self._last_event_name = name
            self._last_event_payload = payload
            self._last_event = payload if payload is not None else name
            return name
        except queue.Empty:
            pass

        evt = self.channel.read_event(timeout=timeout)
        if evt is not None:
            self._last_event_name = str(evt) if not isinstance(evt, bytes) else evt.decode(errors="ignore")
            self._last_event_payload = None
            self._last_event = evt
            return evt
        return None

    def channel_write(self, data: bytes | str) -> None:
        self.channel.write(data)

    def _make_bus_handler(self, name: str):
        def _handler(payload):
            self._event_queue.put((name, payload))

        return _handler

    def close(self) -> None:
        if not self._bus:
            return
        for event_name, handler in self._bus_handlers:
            try:
                self._bus.unsubscribe(event_name, handler)
            except Exception:
                pass
        self._bus_handlers.clear()
