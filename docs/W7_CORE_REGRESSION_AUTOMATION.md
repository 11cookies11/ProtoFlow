# W7-01 核心回归自动化入口

## 目标

- 用一条命令执行核心链路回归门禁并输出汇总结果。
- 覆盖当前已落地的 W4/W5 关键门禁脚本。

## 入口脚本

- `scripts/core_regression_gate.py`

## 执行

```powershell
python scripts/core_regression_gate.py --serial-mode mock --serial-cycles 50
```

输出目录（默认）：

- `artifacts/core_regression/core_regression_summary.json`

## 当前串联步骤

1. `scripts/w4_gate_runner.py`
2. `scripts/dsl_lifecycle_gate.py`
3. `scripts/protocol_replay_gate.py`

## 通过标准

- `core_regression_summary.json` 中 `passed = true`
- 每个 step 的 `passed = true` 且 `exit_code = 0`
