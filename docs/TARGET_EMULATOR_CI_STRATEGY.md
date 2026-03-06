# Target Emulator CI Strategy

## Layered Plan
1. Mock fast regression (per PR/push)
- Runner: `ubuntu-latest`
- Goal: fast deterministic sanity checks without serial driver dependency
- Cases:
  - `scripts/target_emulator_regression.py`
  - `scripts/target_emulator_fault_regression.py`

2. Virtual-serial nightly regression (schedule/dispatch)
- Runner: `windows-latest`
- Goal: verify real serial stack path with com2com pair
- Entry:
  - `scripts/nightly_virtual_serial_regression.ps1`
- Required repo variables:
  - `TARGET_HOST_PORT` (example: `COM11`)
  - `TARGET_DEVICE_PORT` (example: `COM12`)

## Workflow
- File: `.github/workflows/target-emulator-ci.yml`
- Trigger:
  - `push` on `main`
  - `pull_request`
  - `schedule` daily
  - `workflow_dispatch`

## Design Notes
- Nightly job is skipped when virtual serial variables are not configured.
- Mock job remains mandatory to keep quick feedback loop.
