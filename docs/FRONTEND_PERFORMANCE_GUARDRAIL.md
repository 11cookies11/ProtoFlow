# Frontend Performance Guardrail

## Budget Source
- File: `ui/frontend/config/perf_budget.json`
- Script: `ui/frontend/scripts/perf_report.mjs`

## Commands
- Build + budget report:
```bash
npm run build
npm run perf:report
```
- Full frontend gate:
```bash
npm run ci:frontend
```

## Current Budget Keys
- `js_bundle_max_kb`
- `css_bundle_max_kb`
- `js_gzip_max_kb`
- `css_gzip_max_kb`

## Notes
- Budget report checks built assets under `dist/assets`
- If budget fails, process exits with non-zero code
- Bundle budget complements runtime interaction checks, not a replacement
- 2026-03-01 update: App views and CodeMirror runtime are async-split/lazy-loaded, and bundle warning is removed in default build output.
