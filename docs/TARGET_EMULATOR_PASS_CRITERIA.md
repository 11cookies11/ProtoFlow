# Target Emulator Pass Criteria (v0.1 Baseline)

## Scope
- `scripts/target_emulator_regression.py`
- `scripts/target_emulator_fault_regression.py`
- `scripts/runtime_regression_suite.py`

## Required Conditions
1. Functional pass
- All checks in `target_emulator_regression.py` must pass.
- Required: AT baseline response, fallback behavior, artifact generation.

2. Fault injection pass
- All checks in `target_emulator_fault_regression.py` must pass.
- Required: drop-once, jitter response, chunked response, close-after behavior.

3. Runtime integration pass
- `runtime_regression_suite.py` exits with code `0`.
- Includes existing DSL/runtime regressions and target emulator regressions.

4. Artifact integrity
- Emulator artifacts must contain:
  - `raw_log.jsonl`
  - `summary.json`
- `summary.rules_hit` must record at least one hit for a baseline AT rule.

## Stability Targets
- Local repeated run (>=3 times) should keep pass rate at 100%.
- No unexpected exception stack traces in successful runs.
