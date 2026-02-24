# W2 Technical Debt Backlog

## Objective
- Deliver the W2 output for "technical debt grading and scheduling".
- Normalize known debt items from W1 audits into a single execution list.

## Grading Rules
- `blocking`: blocks release-critical path or causes false "working" signal.
- `high`: high user impact or high regression risk; can proceed short-term with mitigation.
- `medium`: important correctness/observability gaps, but not immediate release blocker.
- `low`: docs alignment, reserve features, or non-critical experience issues.

## Backlog (W2 Freeze)

| ID | Debt Item | Source | Grade | Planned Milestone | Due Date | Owner | Acceptance (DoD) |
|---|---|---|---|---|---|---|---|
| TD-001 | Release pipeline may ship fallback page when `frontend/dist` missing | UF-001 | blocking | M1/W2 | 2026-03-04 | you+Codex | Build/release fails hard when dist missing; fallback page is not release-eligible output. |
| TD-002 | Proxy "running" status not bound to real forwarding engine | UF-003 | blocking | M1/W2 | 2026-03-06 | you+Codex | UI state and actual forwarding capability are explicitly aligned; no misleading running state. |
| TD-003 | Runtime/Network/Logs settings mostly persisted but not consumed | UF-004 | blocking | M1/W2 | 2026-03-08 | you+Codex | Parameter mapping table exists; each field is either consumed or hidden/marked unsupported. |
| TD-004 | COM/Serial reconnect and exceptional path stability still partial | W1 module inventory | high | M2/W3-W4 | 2026-03-22 | you+Codex | Exception paths recover; logs provide traceable evidence; target success rate baseline can be measured. |
| TD-005 | UI connection status may drift from backend truth in edge cases | W1 module inventory | high | M2/W3 | 2026-03-15 | you+Codex | No "false connected" state under disconnect/error/reconnect scenarios. |
| TD-006 | Capture pipeline confidence outside Modbus RTU is weak | W1 pending item | high | M2-W3/M4 | 2026-04-05 | you+Codex | Sample replay set and error-rate baseline documented for non-RTU traffic classes. |
| TD-007 | DSL execution observability depth incomplete (state/progress/error consistency) | W1 module inventory | medium | M3/W5 | 2026-03-29 | you+Codex | State/progress/error signals are consistent and verifiable in key scripts. |
| TD-008 | Protocol parser coverage beyond current core use-cases is incomplete | W1 pending item | medium | M3/W5 | 2026-03-29 | you+Codex | Coverage matrix and sample-based pass criteria published and executed. |
| TD-009 | End-to-end regression baseline not formalized for release gate | PROJECT_PLAN W2/W7 | medium | M1-W2 to M5/W7 | 2026-04-12 | you+Codex | Core regression list is executable and linked to release checklist. |
| TD-010 | Docs claim/implementation mismatch for Modbus action support | UF-005 | low | M2 | 2026-03-22 | you+Codex | USER_GUIDE and USER_GUIDE_EN descriptions match runtime behavior. |
| TD-011 | `meter_*` actions documented but not implemented | UF-006 | low | M5 | 2026-04-12 | you+Codex | Docs explicitly mark status as reserved/not implemented with version note. |
| TD-012 | Placeholder/demo paths and partial modules missing frozen completion criteria | W1 pending item | low | M1/W2 | 2026-03-08 | you+Codex | Each `partial` module has frozen DoD and acceptance evidence format. |

## W2 Execution Sequence
1. Close all `blocking` items in W2 window first (`TD-001`~`TD-003`).
2. Start `high` items with COM-first path (`TD-004`, `TD-005`) as M2 entry.
3. Freeze docs and DoD hygiene (`TD-010`, `TD-012`) before W2 closure.

## Tracking Notes
- This file is the single source for debt grading and schedule.
- Detailed implementation records remain in feature-specific docs/PRs.
