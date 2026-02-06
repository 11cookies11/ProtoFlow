from __future__ import annotations

from typing import Dict

from actions.base import ActionBase


class ActionRegistry:
    actions: Dict[str, ActionBase] = {}

    @classmethod
    def register(cls, name: str, action: ActionBase) -> None:
        if not isinstance(action, ActionBase):
            raise TypeError("action must be an ActionBase")
        cls.actions[name] = action

    @classmethod
    def get(cls, name: str) -> ActionBase:
        if name not in cls.actions:
            raise KeyError(f"¶¯×÷Î´×¢²á: {name}")
        return cls.actions[name]
