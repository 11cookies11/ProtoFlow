from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ActionCall:
    name: str
    args: Dict[str, Any] = field(default_factory=dict)


@dataclass
class State:
    name: str
    actions: List[ActionCall] = field(default_factory=list)
    on_event: Dict[str, str] = field(default_factory=dict)
    timeout: Optional[int] = None
    on_timeout: Optional[str] = None
    when: Optional[str] = None
    goto: Optional[str] = None
    else_goto: Optional[str] = None


@dataclass
class StateMachine:
    initial: str
    states: Dict[str, State]


@dataclass
class ScriptAST:
    version: int
    vars: Dict[str, Any]
    channels: Dict[str, Dict[str, Any]]
    state_machine: StateMachine
