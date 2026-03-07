from __future__ import annotations

import logging
import os
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.main_web import _setup_run_logging


def _check(name: str, cond: bool) -> bool:
    print(f"[{'PASS' if cond else 'FAIL'}] {name}")
    return cond


def _contains_all(path: Path, tokens: list[str]) -> bool:
    text = path.read_text(encoding="utf-8")
    return all(token in text for token in tokens)


def _verify_packaging_manifests() -> bool:
    ok = True
    ok &= _check(
        "spec.datas_required",
        _contains_all(
            REPO_ROOT / "ProtoFlow.spec",
            [
                "('ui\\\\frontend\\\\dist', 'ui\\\\frontend\\\\dist')",
                "('config', 'config')",
                "('plugins', 'plugins')",
                "('ui\\\\assets', 'ui\\\\assets')",
                "('VERSION', '.')",
            ],
        ),
    )
    ok &= _check(
        "build_script.datas_required",
        _contains_all(
            REPO_ROOT / "scripts" / "build_windows.ps1",
            [
                '--add-data "ui\\\\frontend\\\\dist;ui\\\\frontend\\\\dist"',
                '--add-data "config;config"',
                '--add-data "plugins;plugins"',
                '--add-data "ui\\\\assets;ui\\\\assets"',
                '--add-data "VERSION;."',
            ],
        ),
    )
    ok &= _check(
        "installer.version_macro",
        _contains_all(
            REPO_ROOT / "installer" / "ProtoFlow.iss",
            [
                "#ifndef MyAppVersion",
                "AppVersion={#MyAppVersion}",
                "OutputBaseFilename=ProtoFlow-{#MyAppVersion}-setup",
            ],
        ),
    )
    return ok


def _verify_runtime_logging() -> bool:
    ok = True
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    old_unraisable = getattr(sys, "unraisablehook", None)
    old_localappdata = os.environ.get("LOCALAPPDATA")

    try:
        with tempfile.TemporaryDirectory(prefix="protoflow_pkg_") as tmp:
            os.environ["LOCALAPPDATA"] = tmp
            log_path = _setup_run_logging()
            print("package_runtime_probe")
            sys.stdout.flush()
            sys.stderr.flush()
            logging.shutdown()

            log_exists = log_path.exists() and log_path.parent.name == "logs"
            ok &= _check("runtime.log_path_created", log_exists)

            content = log_path.read_text(encoding="utf-8") if log_exists else ""
            ok &= _check("runtime.log_contains_probe", "package_runtime_probe" in content)
            for stream in (sys.stdout, sys.stderr):
                handle = getattr(stream, "_file", None)
                if handle is not None and not getattr(handle, "closed", True):
                    handle.close()
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        if old_unraisable is not None:
            sys.unraisablehook = old_unraisable
        if old_localappdata is None:
            os.environ.pop("LOCALAPPDATA", None)
        else:
            os.environ["LOCALAPPDATA"] = old_localappdata

    return ok


def main() -> int:
    ok = True
    ok &= _verify_packaging_manifests()
    ok &= _verify_runtime_logging()
    print(f"RESULT: {'PASSED' if ok else 'FAILED'}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
