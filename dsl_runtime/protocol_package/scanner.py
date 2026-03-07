from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List

import yaml

from dsl_runtime.protocol_package.models import (
    ProtocolPackageManifest,
    ProtocolPackageScanIssue,
    ProtocolPackageScanResult,
)


_REQUIRED_FILES = ("protocol.yaml", "impl.py", "README.md", "vectors.yaml")
_REQUIRED_API = {"send", "recv", "rpc"}


def _issue(result: ProtocolPackageScanResult, level: str, package_dir: Path, message: str) -> None:
    result.issues.append(
        ProtocolPackageScanIssue(
            level=level,
            package_dir=str(package_dir),
            message=message,
        )
    )


def _as_mapping(value: Any, *, field: str) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be a mapping")
    return value


def _as_list(value: Any, *, field: str) -> List[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    return list(value)


def _as_non_empty_str(value: Any, *, field: str) -> str:
    text = str(value).strip() if value is not None else ""
    if not text:
        raise ValueError(f"{field} is required")
    return text


def _validate_manifest(pkg_dir: Path, data: Dict[str, Any]) -> ProtocolPackageManifest:
    protocol_id = _as_non_empty_str(data.get("id"), field="id")
    name = _as_non_empty_str(data.get("name"), field="name")
    version = _as_non_empty_str(data.get("version"), field="version")
    entry = _as_mapping(data.get("entry"), field="entry")
    entry_module = _as_non_empty_str(entry.get("module"), field="entry.module")
    entry_class = _as_non_empty_str(entry.get("class"), field="entry.class")
    api = [str(x).strip() for x in _as_list(data.get("api"), field="api")]
    api_set = {x for x in api if x}
    missing = sorted(_REQUIRED_API - api_set)
    if missing:
        raise ValueError(f"api missing required items: {', '.join(missing)}")
    config_schema = data.get("config_schema") or {}
    if not isinstance(config_schema, dict):
        raise ValueError("config_schema must be a mapping")
    message_schema = data.get("message_schema") or {}
    if not isinstance(message_schema, dict):
        raise ValueError("message_schema must be a mapping")
    return ProtocolPackageManifest(
        pkg_dir=pkg_dir,
        protocol_id=protocol_id,
        name=name,
        version=version,
        entry_module=entry_module,
        entry_class=entry_class,
        api=sorted(api_set),
        config_schema=config_schema,
        message_schema=message_schema,
    )


def _iter_package_dirs(root: Path) -> Iterable[Path]:
    if not root.exists():
        return []
    return [p for p in root.iterdir() if p.is_dir()]


def scan_protocol_packages(root_dir: str | Path) -> ProtocolPackageScanResult:
    root = Path(root_dir).resolve()
    result = ProtocolPackageScanResult()
    seen_ids: Dict[str, Path] = {}
    for pkg_dir in _iter_package_dirs(root):
        missing = [name for name in _REQUIRED_FILES if not (pkg_dir / name).exists()]
        if missing:
            _issue(result, "error", pkg_dir, f"missing required files: {', '.join(missing)}")
            continue
        manifest_path = pkg_dir / "protocol.yaml"
        try:
            data = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
            if not isinstance(data, dict):
                raise ValueError("protocol.yaml root must be a mapping")
            manifest = _validate_manifest(pkg_dir, data)
        except Exception as exc:
            _issue(result, "error", pkg_dir, f"invalid manifest: {exc}")
            continue
        if manifest.protocol_id in seen_ids:
            _issue(
                result,
                "error",
                pkg_dir,
                f"duplicate protocol id '{manifest.protocol_id}' (already in {seen_ids[manifest.protocol_id]})",
            )
            continue
        seen_ids[manifest.protocol_id] = pkg_dir
        result.manifests.append(manifest)
    return result
