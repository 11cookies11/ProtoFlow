from __future__ import annotations

from typing import Dict

from dsl_runtime.actions.base import DslActionBase


class ActionRegistry:
    actions: Dict[str, DslActionBase] = {}

    @classmethod
    def register(cls, name: str, action: DslActionBase) -> None:
        if not isinstance(action, DslActionBase):
            raise TypeError("action must be a DslActionBase")
        cls.actions[name] = action

    @classmethod
    def get(cls, name: str) -> DslActionBase:
        if name not in cls.actions:
            raise KeyError(f"¶¯×÷Î´×¢²á: {name}")
        return cls.actions[name]
