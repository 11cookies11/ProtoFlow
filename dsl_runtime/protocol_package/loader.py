from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from dsl_runtime.protocol_package.models import ProtocolPackageManifest, ProtocolPackageScanIssue
from dsl_runtime.protocol_package.scanner import scan_protocol_packages


@dataclass
class LoadedProtocolPackage:
    manifest: ProtocolPackageManifest
    impl: Any


@dataclass
class ProtocolPackageLoadResult:
    packages: Dict[str, LoadedProtocolPackage]
    issues: List[ProtocolPackageScanIssue]


def _module_to_file(pkg_dir: Path, module_name: str) -> Path:
    parts = [x for x in module_name.split(".") if x]
    if not parts:
        raise ValueError("entry.module is empty")
    return pkg_dir.joinpath(*parts).with_suffix(".py")


def _load_impl_class(manifest: ProtocolPackageManifest) -> Any:
    module_name = f"proto_pkg_{manifest.protocol_id}_{manifest.version.replace('.', '_')}"
    module_file = _module_to_file(manifest.pkg_dir, manifest.entry_module)
    if not module_file.exists():
        raise FileNotFoundError(f"entry module file not found: {module_file}")
    spec = importlib.util.spec_from_file_location(module_name, module_file)
    if spec is None or spec.loader is None:
        raise ImportError(f"unable to create import spec for {module_file}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    cls = getattr(module, manifest.entry_class, None)
    if cls is None:
        raise ImportError(f"entry class not found: {manifest.entry_class}")
    return cls


def _validate_impl_api(impl: Any, manifest: ProtocolPackageManifest) -> None:
    for method in manifest.api:
        fn = getattr(impl, method, None)
        if fn is None or not callable(fn):
            raise TypeError(f"api method missing or not callable: {method}")


def load_protocol_packages(root_dir: str | Path) -> ProtocolPackageLoadResult:
    scan = scan_protocol_packages(root_dir)
    packages: Dict[str, LoadedProtocolPackage] = {}
    issues = list(scan.issues)
    for manifest in scan.manifests:
        try:
            cls = _load_impl_class(manifest)
            impl = cls()
            _validate_impl_api(impl, manifest)
            packages[manifest.protocol_id] = LoadedProtocolPackage(manifest=manifest, impl=impl)
        except Exception as exc:
            issues.append(
                ProtocolPackageScanIssue(
                    level="error",
                    package_dir=str(manifest.pkg_dir),
                    message=f"load failed: {exc}",
                )
            )
    return ProtocolPackageLoadResult(packages=packages, issues=issues)
