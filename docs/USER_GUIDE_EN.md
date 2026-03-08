# ProtoFlow User Guide (Updated)

This guide is designed to help users quickly learn and use ProtoFlow in real work.
By the end, you should be able to:
- start ProtoFlow and complete basic communication debugging
- run a DSL automation script
- write your own script from templates
- troubleshoot common errors

Related docs:
- i18n manual index: [`docs/i18n-manual/README.md`](./i18n-manual/README.md)

## 1. What ProtoFlow Is
ProtoFlow is a communication automation tool, not just a serial terminal.
It models communication as executable workflow steps (DSL), and is suitable for:
- serial / TCP debugging
- protocol-package calls (AT / SCPI / YMODEM / Modbus, etc.)
- automation and production test flows
- structured logging and run artifacts

## 2. Install and Launch

### 2.1 Requirements
- Python 3.11+
- Windows (the current repository and scripts are primarily Windows-oriented)
- available COM ports if you use serial

### 2.2 Install dependencies
```bash
pip install -r requirements.txt
```

### 2.3 Launch desktop app (recommended)
```bash
python main.py
```

Notes:
- `main.py` starts the full Qt + Web frontend desktop UI.
- Runtime logs are written to `%LOCALAPPDATA%/ProtoFlow/logs/`.

## 3. 5-Minute Quick Start (First Run)

1. Launch the app and open the `Manual` page.
2. Select a serial port and baud rate, then connect.
3. Send `AT` (Text mode; enable `+CR/+LF` if required by your device).
4. Confirm you receive `OK` or device response in logs.
5. Switch to `Scripts`, load an example script, and run it.

Recommended examples:
- `scripts/examples/at_command_flow_v01.yaml`
- `scripts/examples/scpi_flow_v01.yaml`

## 4. UI Usage Guide

### 4.1 Manual
Best for live communication debugging.

Main capabilities:
- connect / disconnect serial
- send in Text or HEX mode
- quick command management (create/edit/delete/send)
- IO log view (ASCII/HEX)
- log filtering, pause, clear, export

Practical tips:
- For command-based devices, start with Text mode + `CR/LF`.
- For binary protocols, use HEX mode.
- Always verify link and response in Manual before running automation scripts.

### 4.2 Scripts
Best for repeatable automation flows (send, wait, assert, parse, record).

Main capabilities:
- load/save YAML scripts
- run/stop
- runtime logs
- variable snapshot view
- execution progress

Recommended workflow:
1. Copy a template from `scripts/examples/`.
2. Modify `params` first (port/address/file path).
3. Get a minimal flow running, then add `assert/parse/capture` step by step.

### 4.3 Protocols
Shows available external protocol packages from the `protocols/` directory.

Current behavior:
- list/view protocol package metadata
- UI protocol management is read-only (no create/edit/delete in UI)

### 4.4 Proxy Monitor (Optional)
For dual-serial forwarding and frame capture analysis.

Enable it by either:
- environment variable: `PROTOFLOW_ENABLE_PROXY_MONITOR=1`
- config: `config/app.yaml` with `app.proxy_monitor_enabled: true`

If not enabled, related UI features are hidden/disabled.

### 4.5 Settings
Configure language, theme, serial defaults, network options, and workspace path.

Settings file:
- `%LOCALAPPDATA%/ProtoFlow/config/ui_settings.json`

## 5. DSL Getting Started

## 5.1 Recommended version for new users
Most built-in runnable examples currently use `version: "0.1"`.
For onboarding, start from v0.1 templates first.

## 5.2 Minimal runnable template
```yaml
version: "0.1"

params:
  port: "COM3"
  baud: 115200

session:
  transport: serial
  port: "${port}"
  baud: "${baud}"
  data_bits: 8
  parity: none
  stop_bits: 1
  encoding: ascii
  eol: crlf

defaults:
  timeout_ms: 2000
  retry:
    count: 1
    backoff_ms: 200
    strategy: fixed

steps:
  - id: ping
    name: send
    text: "AT"

  - id: wait_ok
    name: expect
    match:
      type: contains
      pattern: "OK"

  - id: done_assert
    name: assert
    expr: "${last_rx_text} != ''"
    message: "no response"

artifacts:
  dir: "./runs/demo_${now}"
  raw_log: true
  summary_json: true
  report_csv: false
```

## 5.3 Common steps (high-frequency)
- `send`: send text/hex payload
- `expect`: wait and match response (contains/regex/startswith)
- `sleep`: delay
- `capture`: regex extraction to variable
- `assert`: condition assertion
- `if` / `loop`: control flow
- `parse` / `path`: structured parsing and field extraction
- `measure` / `assert_range`: metric record and range check
- `protocol.rpc` / `protocol.send` / `protocol.recv`: call external protocol packages
- `switch_session`: switch runtime session settings
- `exec` / `file`: controlled execution (guarded by security allowlists)

## 5.4 Protocol call example (AT)
```yaml
- id: at_ping
  name: protocol.rpc
  protocol: at_command
  request:
    cmd: "AT"
    eol: "crlf"
    expect:
      status: "ok"
  save_as: at_result

- id: assert_at
  name: assert
  expr: "${at_result.ok}"
  message: "AT command failed"
```

## 6. Artifacts and Logs
Script run artifacts under `artifacts.dir` may include:
- `raw_log.jsonl`: step-by-step runtime details
- `summary.json`: overall result, error code, variable snapshot
- `report.csv`: optional report export

Desktop runtime logs:
- `%LOCALAPPDATA%/ProtoFlow/logs/web_ui_*.log`

## 7. Troubleshooting

### 7.1 Connection failed
- check if the serial port is already occupied
- verify baud/parity/stop bits
- validate IO in Manual first, then run scripts

### 7.2 expect timeout
- increase `timeout_ms`
- verify `match.pattern`
- check if target requires `CR/LF`

### 7.3 Empty variable causes assert failure
- verify `capture` regex and group index
- inspect `last_rx_text` in logs

### 7.4 exec/file rejected
- enable and configure allowlists in `security`
- typical codes: `EXEC_NOT_ALLOWED`, `FILE_NOT_ALLOWED`

### 7.5 Proxy Monitor not visible
- verify `proxy_monitor_enabled` is enabled
- restart the app

## 8. Best Practices
- manual first, automation second: verify link in Manual before Scripts
- iterate in small steps: add 1-2 steps each change and run immediately
- assert critical path early: handshake, key responses, output fields
- solidify reusable templates under `scripts/examples/` or your team template repo

## 9. Related Docs
- project overview: `README.md`
- Chinese user guide: `docs/USER_GUIDE.md`
- v0.1 quick reference: `docs/YAML_DSL_V01_QUICKSTART.md`
- v0.2 spec/migration: `docs/YAML_DSL_V02_SCHEMA_SPEC.md`, `docs/YAML_DSL_V02_MIGRATION_AND_BEST_PRACTICES.md`
- protocol package developer guide: `docs/PROTOCOL_PACKAGE_DEVELOPER_GUIDE.zh-CN.md`
