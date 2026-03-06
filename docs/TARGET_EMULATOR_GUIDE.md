# Target Emulator Guide

## Goal
- Provide standalone target-side test code independent from ProtoFlow runtime.
- Validate DSL behaviors via serial/tcp interaction with deterministic responses and fault injection.

## Directory
- `tools/target_emulator/`
- `tools/target_emulator/scenarios/`
- `scripts/target_emulator.py`
- `scripts/target_emulator_regression.py`
- `scripts/run_target_with_dsl.ps1`
- `scripts/examples/target_at_smoke_v02.yaml`

## Modes
- `serial`: pair with com2com or real UART.
- `tcp`: target emulator listens as TCP server.
- `mock`: internal regression mode (used by `target_emulator_regression.py`).

## Scenario Schema (v1)
```yaml
version: "1"
meta:
  name: "AT Basic"
  description: "..."
transport_defaults:
  encoding: "utf-8"
  eol: "crlf"      # none|cr|lf|crlf
rules:
  - id: at_ping
    when:
      type: exact  # contains|exact|startswith|regex
      pattern: "AT"
    respond:
      text: "OK"   # or hex: "4F4B"
      eol: "crlf"  # optional, defaults to transport_defaults.eol
    delay_ms: 10
    drop: false
    close_after: false
    once: false
fallback:
  respond:
    text: "ERROR"
```

## Quick Start (Serial + com2com)
1. Create virtual pair, e.g. `COM11 <-> COM12`.
2. Run:
```powershell
.\scripts\run_target_with_dsl.ps1 -HostPort COM11 -TargetPort COM12
```
3. Check output:
- DSL artifacts in `runs/target_at_smoke_*`
- Emulator artifacts in `runs/target_emu_*`

## Regression
```powershell
.\.venv\Scripts\python.exe scripts\target_emulator_regression.py
```

## Notes
- Emulator is transport-level only; no dependency on UI/web bridge.
- Fault cases can be modeled by `drop`, `delay_ms`, `once`, `close_after`.
