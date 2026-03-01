# Frontend Baseline Audit (2026-03-01)

## Scope
- Frontend path: `ui/frontend/src`
- Focus:
  - Runtime hardcoded values inventory
  - Interaction failure inventory (buttons/dropdowns/modal)
  - Desktop shell performance baseline template

## Runtime Hardcoded Inventory
- Cleared:
  - `COMx/baud/host/port` default values are centralized in `src/config/runtimeDefaults.ts`.
  - Serial display normalization uses `src/utils/serialPort.ts`.
  - App version display reads from bridge (`get_app_version`) with fallback.
- Pending follow-up:
  - Non-runtime sample values in docs/examples remain intentionally hardcoded for user guidance.

## Interaction Issue Inventory
- Fixed in this iteration:
  - `ProxyCaptureToolbar`:
    - Search input now emits `update:search-keyword`.
    - "Continue capture" button now emits `resume-capture`.
    - Settings button now emits `open-settings`.
  - `ProxyCaptureFooter`:
    - Pagination buttons now emit `page-first/page-prev/page-next/page-last`.
    - Export button now emits `export`.
    - Disabled state now reflects page boundary.
  - `ProxyCaptureDetails`:
    - Copy hex button now emits `copy-hex`.
    - Action buttons now emit `open-rule`.
    - Copy button has disabled/tooltip behavior when no active frame.
- Added regression tests:
  - `src/components/proxy/ProxyCaptureToolbar.test.ts`
  - `src/components/proxy/ProxyCaptureFooter.test.ts`
  - `src/components/proxy/ProxyCaptureDetails.test.ts`

## Desktop Shell Performance Baseline Template
- Environment:
  - App build: release candidate build from `npm run build`
  - Device: desktop shell host machine
  - Duration: 3 minutes continuous operation per page
- Scenarios:
  - Manual page: connect/disconnect, dropdown open/select, log burst append
  - Proxy page: open capture modal, search/filter, page navigation, detail panel operations
  - Settings page: tab switch, save/discard
- Metrics to record:
  - Dropdown open latency P95 (target `< 100ms`)
  - First visible feedback of primary actions (target `< 120ms`)
  - Scroll frame drop ratio (target `< 5%`)
  - Median FPS during continuous operation (target `>= 50`)
  - Memory trend (no sustained abnormal growth)

## Execution Rule
- Per PR:
  - `npm run ci:frontend`
- Release candidate:
  - Run matrix in `docs/FRONTEND_INTERACTION_TEST_MATRIX.md`
  - Fill the baseline template above and attach result to release notes
