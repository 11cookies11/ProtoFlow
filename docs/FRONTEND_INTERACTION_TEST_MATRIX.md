# Frontend Interaction Test Matrix

## Scope
- UI: `ManualView`, `ScriptsView`, `ProxyMonitorView`, `DropdownSelect`, `LogStream`
- Runtime path: WebBridge -> Vue state -> render
- Baseline: desktop shell first, browser as secondary

## Core Scenarios
- Serial dropdown usability
  - Ports available: can open, select, and display normalized `COMx`
  - Ports unavailable: dropdown still opens with fallback options
  - Connected/connecting: disabled state and reason are visible
- Connection flow consistency
  - Connect button transitions `disconnected -> connecting -> connected`
  - Disconnect returns to `disconnected` and refreshes channel list
- Proxy capture panel
  - Open/close capture modal from proxy card
  - Frame filter (`all/rx/tx/error`) reflects in table list
  - Select frame updates right details panel
- Logging behavior
  - Comm/script logs append without UI freeze during burst input
  - Auto-scroll keeps tail pinned when enabled
  - Manual scroll does not force-jump if auto-scroll disabled
- Modal and dropdown behavior
  - `Esc` closes open dropdown/modals
  - Clicking outside closes dropdown/modal as expected
  - Disabled controls provide visible reason text or title

## Regression Checklist
- No runtime hardcoded version/build date in visible UI
- Port normalization applied before connect/create/update flows
- Long list rendering uses windowed strategy in `Proxy capture` and `LogStream`
- `npm run ci:frontend` must pass before merge

## Execution Cadence
- Per PR: run `npm run ci:frontend`
- Release candidate: run manual matrix on desktop shell
