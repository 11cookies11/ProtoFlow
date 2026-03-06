from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from config_persistence_regression import main as cfg_main
from script_runner_regression import main as runner_main
from target_emulator_fault_regression import main as target_fault_main
from target_emulator_regression import main as target_main
from v01_dsl_regression import main as dsl_main
from protocol_package_test_suite import main as protocol_pkg_main
from yaml_dsl_capability_suite import main as dsl_cap_main
from yaml_dsl_target_full_regression import main as target_full_main


def _run(name: str, fn) -> bool:
    try:
        code = int(fn())
    except Exception as exc:
        print(f"[FAIL] {name}: {exc}")
        return False
    ok = code == 0
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    return ok


def main() -> int:
    ok = True
    ok &= _run("v01_dsl_regression", dsl_main)
    ok &= _run("script_runner_regression", runner_main)
    ok &= _run("config_persistence_regression", cfg_main)
    ok &= _run("target_emulator_regression", target_main)
    ok &= _run("target_emulator_fault_regression", target_fault_main)
    ok &= _run("protocol_package_test_suite", protocol_pkg_main)
    ok &= _run("yaml_dsl_capability_suite", dsl_cap_main)
    ok &= _run("yaml_dsl_target_full_regression", target_full_main)
    print(f"RESULT: {'PASSED' if ok else 'FAILED'}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
