# W2 Regression Baseline (Logs / Connect / RX-TX)

## Goal
- Provide an executable baseline list for W2 regression.
- Cover the minimum stable chain:
  - Channel connect/disconnect
  - Data send/receive visibility
  - Script lifecycle and status propagation
  - Settings effectiveness on COM-first path

## Environment Baseline
- Platform: Windows 10/11
- Runtime: Python 3.11+
- UI host: Qt WebEngine entry (`python main.py`)
- Device side:
  - Serial loopback or controlled test device
  - Optional TCP echo endpoint for non-priority checks

## Test Cases

| ID | Area | Preconditions | Steps | Expected |
|---|---|---|---|---|
| RB-001 | App startup | Frontend dist present | Start app from `main.py` | Main window loads, no fallback page used in release workflow. |
| RB-002 | Serial port list | At least 1 COM visible | Open channel selector / refresh list | COM list is returned and selectable. |
| RB-003 | Serial connect basic | Valid COM + baud | Connect via `connect_serial` | `channel_update.status=connected`, status log shows connected target. |
| RB-004 | Serial connect advanced | Valid COM + advanced params | Connect via `connect_serial_advanced` with parity/stopbits/timeouts | Connected state preserved and selected params echoed in channel details. |
| RB-005 | Serial disconnect | Active serial connection | Trigger disconnect | `comm_status` indicates disconnected; UI state transitions to disconnected. |
| RB-006 | Send text | Active serial connection | Send text payload with CR/LF variations | TX log line appears; payload content is visible in text mode. |
| RB-007 | Send hex | Active serial connection | Send valid hex payload | TX log line appears with expected hex bytes. |
| RB-008 | Invalid hex guard | Active serial connection | Send malformed hex string | No crash; warning is emitted (`invalid hex string`). |
| RB-009 | RX visibility | Loopback or echo response | Send payload and wait RX | RX log appears with timestamp and payload; channel rx_bytes increments. |
| RB-010 | Batch fallback path | Disable direct rx/tx signal path (if applicable) | Receive stream and consume `comm_batch` | Logs still ingest correctly with kind `RX/TX/FRAME/CAPTURE`. |
| RB-011 | Script run lifecycle | Valid minimal DSL yaml | Run script then stop script | `script_state/script_progress/script_log` are emitted; stop works without deadlock. |
| RB-012 | Settings load/save | Existing settings file or defaults | Save settings, restart app, reload settings | Persisted settings are loaded consistently. |
| RB-013 | Network setting effectiveness | Modify `network.tcpTimeoutMs` | Save settings then connect TCP to unreachable endpoint | Connect timeout behavior follows configured timeout window. |
| RB-014 | Capture start/stop | Active channel | Start capture then stop capture | `capture.control` start/stop path works; capture frames can be emitted and consumed. |
| RB-015 | Channel update throttling | Active RX/TX traffic | Observe UI updates over >10s traffic | No UI flood; periodic updates continue with tx/rx byte growth. |

## Evidence Template (per case)
- Result: `pass` / `fail`
- Build/commit: `<hash>`
- Tester/date: `<name> / YYYY-MM-DD`
- Logs:
  - Key UI status line
  - Key bridge signal payload snippet
  - Error/warn snippet (if any)

## Exit Criteria (W2)
- All `RB-001`~`RB-015` executed once on baseline environment.
- All failed cases have issue links and owner.
- Blocking failures must be fixed or explicitly risk-accepted before entering M2.
