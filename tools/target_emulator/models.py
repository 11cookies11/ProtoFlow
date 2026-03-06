from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class MatchRule:
    type: str
    pattern: str


@dataclass
class ResponseSpec:
    text: Optional[str] = None
    hex: Optional[str] = None
    eol: Optional[str] = None


@dataclass
class ScenarioRule:
    id: str
    when: MatchRule
    respond: Optional[ResponseSpec] = None
    delay_ms: int = 0
    drop: bool = False
    close_after: bool = False
    once: bool = False
    enabled: bool = True
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Scenario:
    version: str
    name: str
    description: str = ""
    encoding: str = "utf-8"
    eol: str = "crlf"
    rules: List[ScenarioRule] = field(default_factory=list)
    fallback: Optional[ResponseSpec] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EmulatorConfig:
    mode: str
    artifacts_dir: str
    serial_port: Optional[str] = None
    serial_baud: int = 115200
    tcp_host: str = "127.0.0.1"
    tcp_port: int = 19001
    read_chunk: int = 256
    read_timeout: float = 0.1
