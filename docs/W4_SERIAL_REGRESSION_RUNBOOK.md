# W4-01 Serial Reliability Gate Runbook

## Goal

- Provide an executable gate for `W4-01` (COM/Serial stability).
- Measure connect/reconnect success rate and enforce pass threshold (`>=99%`).

## Script

- Path: `scripts/serial_reliability_gate.py`
- Output: JSON report to stdout (and optional `--json-out` file).

## Mode 1: Mock Gate (Recommended for local dry run)

```powershell
python scripts/serial_reliability_gate.py --mode mock --cycles 200 --threshold 99 --json-out artifacts/w4_mock_gate.json
```

Optional fault injection:

```powershell
python scripts/serial_reliability_gate.py --mode mock --cycles 200 --inject-drop-every 20 --fail-open-every 0
```

## Mode 2: Real COM Gate (Release evidence)

```powershell
python scripts/serial_reliability_gate.py --mode real --port COM5 --baud 115200 --cycles 300 --threshold 99 --json-out artifacts/w4_real_gate.json
```

Recommended preconditions:

- Stable hardware and cable.
- Fixed serial params (`8N1`, expected baud).
- No other process holding the same COM port.

## Pass Criteria

- `connect_success_rate >= threshold`
- If reconnect checks are enabled:
  - `reconnect_success_rate >= threshold`

## Report Fields

- `cycles`, `connect_ok`, `connect_fail`, `connect_success_rate`
- `reconnect_checks`, `reconnect_ok`, `reconnect_fail`, `reconnect_success_rate`
- Event counters:
  - `comm.connecting`
  - `comm.connected`
  - `comm.disconnected`
  - `comm.error`

## Notes

- `mock` mode validates runtime behavior deterministically without real hardware.
- `real` mode results should be attached to release evidence for W4 gate.
