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
class ChartSpec:
    id: str
    title: str
    bind: str
    chart_type: str = "line"  # line | scatter3d
    bind_x: Optional[str] = None
    bind_y: Optional[str] = None
    bind_z: Optional[str] = None
    group: Optional[str] = None
    separate: bool = False
    max_points: int = 1000


@dataclass
class ControlInputSpec:
    name: str
    label: str
    itype: str
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    step: Optional[float] = None
    default: Optional[object] = None
    options: List[str] = field(default_factory=list)
    placeholder: Optional[str] = None


@dataclass
class ControlActionSpec:
    name: str
    emit: str
    label: str


@dataclass
class ControlSpec:
    id: str
    title: str
    separate: bool = True
    inputs: List[ControlInputSpec] = field(default_factory=list)
    actions: List[ControlActionSpec] = field(default_factory=list)


@dataclass
class LayoutNode:
    type: str  # "split" | "leaf"
    orientation: Optional[str] = None  # horizontal | vertical for split
    children: List["LayoutNode"] = field(default_factory=list)
    charts: List[str] = field(default_factory=list)
    controls: List[str] = field(default_factory=list)


@dataclass
class UIConfig:
    charts: List[ChartSpec] = field(default_factory=list)
    controls: List[ControlSpec] = field(default_factory=list)
    layout: Optional[LayoutNode] = None


@dataclass
class SessionConfig:
    transport: str
    port: str
    baud: int = 115200
    data_bits: int = 8
    parity: str = "none"
    stop_bits: int = 1
    encoding: str = "ascii"
    eol: str = "none"
    open_timeout_ms: int = 3000
    read_timeout_ms: int = 200


@dataclass
class RetryPolicy:
    count: int = 0
    backoff_ms: int = 0
    strategy: str = "fixed"


@dataclass
class DefaultsConfig:
    timeout_ms: int = 2000
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    drain_before_expect: bool = False
    consume_on_match: bool = True


@dataclass
class ArtifactsConfig:
    dir: str = "./runs"
    raw_log: bool = True
    summary_json: bool = True
    report_csv: bool = False


@dataclass
class ScriptAST:
    version: str
    params: Dict[str, Any] = field(default_factory=dict)
    vars: Dict[str, Any] = field(default_factory=dict)
    session: Optional[SessionConfig] = None
    defaults: DefaultsConfig = field(default_factory=DefaultsConfig)
    steps: List[Dict[str, Any]] = field(default_factory=list)
    artifacts: ArtifactsConfig = field(default_factory=ArtifactsConfig)
    security: Dict[str, Any] = field(default_factory=dict)
    # Legacy fields kept as optional placeholders while v0.1 runtime is phased in.
    channels: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    state_machine: Optional[StateMachine] = None
    ui: UIConfig = field(default_factory=UIConfig)
