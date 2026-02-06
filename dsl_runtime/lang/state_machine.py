from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from dsl_runtime.lang.ast_nodes import State


@dataclass
class StateMachineDef:
    initial: str
    states: Dict[str, State]
