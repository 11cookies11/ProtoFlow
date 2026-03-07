from __future__ import annotations

from pathlib import Path
import sys
from unittest.mock import patch

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ui.desktop.script_runner_qt import ScriptRunnerQt
from dsl_runtime.engine.channels import DummyChannel


YAML_OK = """
version: 0.1
session:
  transport: serial
  port: COM_TEST
  baud: 115200
steps:
  - name: sleep
    duration_ms: 10
""".strip()

YAML_ERROR = """
version: 0.1
session:
  transport: serial
  port: COM_TEST
  baud: 115200
steps:
  - name: does_not_exist
""".strip()


def _run_case(yaml_text: str, stop_before_run: bool = False):
    runner = ScriptRunnerQt(yaml_text)
    logs: list[str] = []
    states: list[str] = []
    progress: list[int] = []
    runner.sig_log.connect(lambda x: logs.append(x))
    runner.sig_state.connect(lambda x: states.append(x))
    runner.sig_progress.connect(lambda x: progress.append(int(x)))
    if stop_before_run:
        runner.stop()
    with patch("ui.desktop.script_runner_qt.build_channels", return_value={"default": DummyChannel()}):
        runner.run()
    return logs, states, progress


def main() -> int:
    checks: list[tuple[str, bool]] = []

    logs_ok, states_ok, progress_ok = _run_case(YAML_OK, stop_before_run=False)
    checks.append(("ok.running_state", "__running__" in states_ok))
    checks.append(("ok.finished_state", "__finished__" in states_ok))
    checks.append(("ok.finished_log", any("Script finished" in x for x in logs_ok)))
    checks.append(("ok.progress_100", any(v >= 100 for v in progress_ok)))

    logs_stop, states_stop, _ = _run_case(YAML_OK, stop_before_run=True)
    checks.append(("stop.running_state", "__running__" in states_stop))
    checks.append(("stop.stopped_state", "__stopped__" in states_stop))
    checks.append(("stop.stopped_log", any("Script stopped" in x for x in logs_stop)))

    logs_err, states_err, _ = _run_case(YAML_ERROR, stop_before_run=False)
    checks.append(("err.running_state", "__running__" in states_err))
    checks.append(("err.error_state", "__error__" in states_err))
    checks.append(("err.error_log", any(x.startswith("[ERROR]") for x in logs_err)))

    ok = True
    for name, passed in checks:
        print(f"[{'PASS' if passed else 'FAIL'}] {name}")
        ok = ok and passed
    print(f"RESULT: {'PASSED' if ok else 'FAILED'}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
