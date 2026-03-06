from __future__ import annotations

from pathlib import Path

from dsl_runtime.protocol_package import load_protocol_packages, run_protocol_vectors
from scripts.protocol_package_regression import main as regression_main


def _assert_load_ok(root: Path) -> None:
    load = load_protocol_packages(root)
    errors = [x for x in load.issues if x.level == "error"]
    assert not errors, f"load issues: {[x.message for x in errors]}"
    assert "modbus_rtu" in load.packages, "modbus_rtu package missing"
    assert "modbus_ascii" in load.packages, "modbus_ascii package missing"
    assert "modbus_tcp" in load.packages, "modbus_tcp package missing"
    assert "xmodem" in load.packages, "xmodem package missing"


def _assert_vectors_ok(root: Path, protocol_id: str) -> None:
    result = run_protocol_vectors(root, protocol_id)
    assert result.ok, f"vectors failed: {protocol_id}"


def main() -> int:
    root = Path("protocols").resolve()
    _assert_load_ok(root)
    _assert_vectors_ok(root, "modbus_rtu")
    _assert_vectors_ok(root, "modbus_ascii")
    _assert_vectors_ok(root, "modbus_tcp")
    _assert_vectors_ok(root, "xmodem")
    assert regression_main() == 0, "protocol_package_regression failed"
    print("protocol package test suite: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
