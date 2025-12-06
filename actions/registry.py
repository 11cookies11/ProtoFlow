from __future__ import annotations

from typing import Any, Callable, Dict


class ActionRegistry:
    actions: Dict[str, Callable[..., Any]] = {}

    @classmethod
    def register(cls, name: str, fn: Callable[..., Any]) -> None:
        cls.actions[name] = fn

    @classmethod
    def get(cls, name: str) -> Callable[..., Any]:
        if name not in cls.actions:
            raise KeyError(f"动作未注册: {name}")
        return cls.actions[name]
