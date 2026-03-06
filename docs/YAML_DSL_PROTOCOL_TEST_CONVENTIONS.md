# YAML-DSL Protocol Test Conventions

## Directory Convention
- Regression scripts: `scripts/*_regression.py`
- DSL examples: `scripts/examples/*.yaml`
- Target emulator scenarios: `tools/target_emulator/scenarios/*.yaml`
- Reports (runtime generated): `runs/` (git ignored)
- Frozen baseline snapshots (optional docs): `docs/target-emulator-baseline/` (git ignored)

## Naming Convention
- Script name: `<domain>_<scope>_regression.py`
  - example: `yaml_dsl_target_full_regression.py`
- Scenario name: `<intent>_<fault>.yaml` or `<protocol>_<mode>.yaml`
  - example: `retry_expect_window.yaml`
- Report file:
  - summary: `*_summary.json`
  - full report: `*_report.json`

## Case ID Convention
- Format: `<layer>.<feature>.<variant>`
  - example: `dsl.retry.expect_window`

## Result Contract
- Every regression should emit:
  - console checks (`[PASS]/[FAIL]`)
  - final line: `RESULT: PASSED|FAILED`
  - structured report JSON compliant with `scripts/test_result_schema.json`

## Exit Code
- `0`: all checks passed
- `2`: any check failed or unexpected error

## CI Mapping
- PR fast set:
  - `scripts/v01_dsl_regression.py`
  - `scripts/target_emulator_regression.py`
  - `scripts/protocol_package_test_suite.py`
  - `scripts/yaml_dsl_capability_suite.py`
  - `scripts/yaml_dsl_combo_regression.py`
  - `scripts/yaml_dsl_fault_injection_regression.py`
- Nightly set:
  - `scripts/runtime_regression_suite.py`
- Weekly soak set:
  - `scripts/yaml_dsl_stability_regression.py`
  - `scripts/yaml_dsl_performance_baseline.py`
