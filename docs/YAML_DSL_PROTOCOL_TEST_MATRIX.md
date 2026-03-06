# YAML-DSL + Protocol Package Test Matrix

## Scope
- DSL runtime: `v0.2` (兼容 `v0.1`)
- Protocol packages:
  - `at_command`
  - `scpi`
  - `ymodem`
  - `xmodem`
  - `modbus_rtu`
  - `modbus_ascii`
  - `modbus_tcp`
- Target emulator modes:
  - `mock`
  - `serial` (real/com2com)
  - `tcp`

## Axes
- Capability axis: 功能点
- Transport axis: mock/serial/tcp
- Package axis: protocol package
- Fault axis: timeout/jitter/drop/chunk/disconnect
- Artifact axis: raw_log/summary/report/result model

## DSL Capability Coverage
| Capability | Required Cases | Current Entry |
|---|---|---|
| `session/send/expect/sleep/capture/assert` | normal + timeout + regex + capture fail | `scripts/v01_dsl_regression.py` |
| `retry/on_fail` | fixed + exponential + hook side effect | `scripts/v01_dsl_regression.py` / `scripts/yaml_dsl_target_full_regression.py` |
| `if/loop/switch_session(dry_run)` | branch true/false + until + times | `scripts/v01_dsl_regression.py` / `scripts/yaml_dsl_target_full_regression.py` |
| `parse(json|kv|csv)/path/measure/assert_range` | normal + path fail + range fail | `scripts/v01_dsl_regression.py` / `scripts/yaml_dsl_target_full_regression.py` |
| `exec/file security` | allow + deny + path guard | `scripts/v01_dsl_regression.py` / `scripts/yaml_dsl_target_full_regression.py` |
| `protocol.send/recv/rpc` | contract + error mapping + timeout | `scripts/protocol_package_test_suite.py` / `scripts/yaml_dsl_target_full_regression.py` |
| Artifacts | raw/summary/csv + result schema mapping | `scripts/*regression.py` |

## Protocol Package Coverage
| Package | send | recv | rpc | normal | timeout | error-path | vectors |
|---|---:|---:|---:|---:|---:|---:|---:|
| at_command | Y | Y | Y | Y | Y | Y | Y |
| scpi | Y | Y | Y | Y | Y | Y | Y |
| ymodem | Y | Y | Y | Y | Y | Y | Y |
| xmodem | Y | Y | Y | Y | Y | Y | Y |
| modbus_rtu | Y | Y | Y | Y | Y | Y | Y |
| modbus_ascii | Y | Y | Y | Y | Y | Y | Y |
| modbus_tcp | Y | Y | Y | Y | Y | Y | Y |

## Fault Injection Coverage
| Fault Type | Target Scenario | Expected Validation |
|---|---|---|
| timeout | `retry_expect_window.yaml` | retry hit + eventual pass/fail correctness |
| drop | `fault_injection_matrix.yaml` | missing response handling |
| jitter | `fault_injection_matrix.yaml` | timeout window tolerance |
| chunk | `fault_injection_matrix.yaml` | parser/expect robustness |
| close/disconnect | `fault_injection_matrix.yaml` | graceful error + report |

## Entry Points
- Fast (local/PR): `scripts/runtime_regression_suite.py`
- Full DSL + target: `scripts/yaml_dsl_target_full_regression.py`
- Package vectors: `scripts/protocol_package_test_suite.py`
- Emulator fault: `scripts/target_emulator_fault_regression.py`
- Nightly serial: `scripts/nightly_virtual_serial_regression.ps1`
