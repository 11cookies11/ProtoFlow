# W4-03 通信缺陷收敛台账（P0/P1）

## 目标

- 统一跟踪 COM/Serial 主链路的 P0/P1 缺陷。
- 明确每项缺陷的当前状态、证据与下一步动作。

## 台账

| 缺陷ID | 等级 | 问题描述 | 当前状态 | 证据 | 下一步 |
|---|---|---|---|---|---|
| TD-004 | P0 | 串口异常与重连路径稳定性不足 | in_progress | `infra/comm/serial_manager.py`（重连防重入、退避、停止信号）；`scripts/serial_reliability_gate.py`；`docs/W4_SERIAL_REGRESSION_RUNBOOK.md` | 在真实 COM 环境跑 `W4-01` 300 cycles，补充门禁结果 |
| TD-005 | P0 | UI 连接状态与后端状态漂移 | done | `infra/comm/communication_manager.py`（`comm.connecting`）；`ui/desktop/web_bridge.py`；`ui/frontend/src/App.vue`；`ui/frontend/src/components/ManualView.vue` | 回归关注“连接中/重连中”状态是否误判 |
| RB-014 | P1 | Capture 开关链路缺少自动化校验 | done | `scripts/capture_pipeline_gate.py`；`docs/W4_CAPTURE_VALIDATION_RUNBOOK.md` | 纳入发版前回归执行清单 |
| TD-006 | P1 | 非 Modbus RTU 抓包置信度不足 | in_progress | `app/packet_engine.py` 当前仅内建 Modbus 识别，未知协议走 `Unknown` | 补充样例回放集，建立误报率基线（M4） |

## 收敛规则

1. P0 必须在 M2 结束前进入 `done` 或明确风险接受结论。
2. P1 至少要有可执行门禁或回归脚本，不能只停留在人工描述。
3. 每次状态变更必须附一条“可复现证据”（脚本输出、日志或代码路径）。

## 一键门禁

```powershell
python scripts/w4_gate_runner.py --serial-mode mock --serial-cycles 200 --out-dir artifacts
```

输出：

- `artifacts/w4_serial_gate.json`
- `artifacts/w4_capture_gate.json`
- `artifacts/w4_gate_summary.json`
