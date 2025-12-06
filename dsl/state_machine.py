from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from dsl.ast_nodes import State


@dataclass
class StateMachineDef:
    initial: str
    states: Dict[str, State]
