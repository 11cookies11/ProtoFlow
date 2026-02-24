# W4-02 Capture Pipeline Validation Runbook

## Goal

- Validate `capture.control` start/stop chain.
- Validate `capture.frame` can be produced and consumed reliably.
- Validate capture channel filter behavior.

## Script

- Path: `scripts/capture_pipeline_gate.py`

## Run

```powershell
python scripts/capture_pipeline_gate.py
```

带结果落盘：

```powershell
python scripts/capture_pipeline_gate.py --json-out artifacts/w4_capture_gate.json
```

## Pass Criteria

- `start_stop_ok = true`
- `frame_emit_ok = true`
- `channel_filter_ok = true`
- `passed = true`

## What It Checks

1. Start capture (`capture.control: start`) then publish `comm.tx` / `comm.rx`.
2. Verify `capture.frame` is emitted.
3. Stop capture (`capture.control: stop`) then publish traffic again.
4. Verify no new capture frame is emitted after stop.
5. Start capture with mismatched target channel and verify frames are filtered out.

## Notes

- This gate is runtime-level and does not require UI interaction.
- For release evidence, keep one command output snapshot in the validation record.
- 可配合一键汇总命令：
  - `python scripts/w4_gate_runner.py --serial-mode mock --out-dir artifacts`
