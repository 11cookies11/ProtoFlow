from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class ProtocolPackageManifest:
    pkg_dir: Path
    protocol_id: str
    name: str
    version: str
    entry_module: str
    entry_class: str
    api: List[str] = field(default_factory=list)
    config_schema: Dict[str, Any] = field(default_factory=dict)
    message_schema: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProtocolPackageScanIssue:
    level: str
    package_dir: str
    message: str


@dataclass
class ProtocolPackageScanResult:
    manifests: List[ProtocolPackageManifest] = field(default_factory=list)
    issues: List[ProtocolPackageScanIssue] = field(default_factory=list)
