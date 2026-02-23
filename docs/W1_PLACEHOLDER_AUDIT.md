# W1 未完成功能评估（预填版）

## 评估口径

- `confirmed`: 代码证据明确显示未完成/占位。
- `likely`: 现有代码高度暗示未完成，需集成确认。
- 优先级：`P0`（影响主链路/易误导）、`P1`（重要但可排后）、`P2`（文档或体验层）。

## 评估结果清单

| ID | 功能点 | 证据 | 当前状态 | 影响 | 优先级 | 建议里程碑 | 结论 |
|---|---|---|---|---|---|---|---|
| UF-001 | Web fallback 占位页 | `ui/desktop/web_window.py:76`, `ui/desktop/web_window.py:77`, `ui/assets/web/index.html:58` | 当 `frontend/dist` 不存在时回退到占位页 | 发布流程若漏打包，用户会误判“应用可用” | P0 | M4 | confirmed |
| UF-002 | 图表数据含 demo 随机源 | `dsl_runtime/engine/chart_runtime.py:33` | `_tick` 周期发随机数据 | 数据真实性不足，影响监控可信度 | P1 | M4 | confirmed |
| UF-003 | Proxy 配对“运行中”主要是状态落盘 | `ui/desktop/web_bridge.py:382`, `ui/desktop/web_bridge.py:388`, `ui/desktop/web_bridge.py:389` | 只看到状态切换与配置保存，未见真实转发引擎 | 监控/透传能力可能被高估 | P0 | M4 | confirmed |
| UF-004 | Runtime/Network/Logs 多项设置仅保存未生效 | `ui/desktop/web_bridge.py:789`, `ui/desktop/web_bridge.py:790`, `ui/desktop/web_bridge.py:800`；全局搜索仅命中配置读写 | 参数可在 UI 保存，但未见被通信/运行时消费 | 用户配置与实际行为不一致 | P0 | M4 | confirmed |
| UF-005 | 文档与实现冲突：Modbus 动作“未实现”描述过期 | 文档：`docs/USER_GUIDE.md:118`, `docs/USER_GUIDE_EN.md:187`；实现：`dsl_runtime/actions/dsl_protocol_actions.py:203`, `ui/desktop/script_runner_qt.py:126` | 代码已注册 `modbus_read/write`，文档仍写未实现 | 误导使用者与测试范围定义 | P1 | M2 | confirmed |
| UF-006 | meter_* 动作仅文档出现，代码未实现 | `docs/USER_GUIDE.md:301`, `docs/USER_GUIDE_EN.md:354`；代码全局无实现 | 文档预留项，无运行时能力 | 预期落差，影响脚本设计 | P2 | M5 | confirmed |

## 额外观察（非缺陷，需澄清）

| ID | 观察项 | 证据 | 说明 | 建议 |
|---|---|---|---|---|
| OBS-001 | DSL 文档存在“已实现/未实现”混写 | `docs/USER_GUIDE.md:118`, `docs/USER_GUIDE.md:121` | 同一章节有冲突描述 | 统一术语并按版本标注 |
| OBS-002 | DummyChannel 为演示通道 | `dsl_runtime/engine/channels.py` 中 `DummyChannel` | 这是合理设计，但需标明使用边界 | 文档中明确“仅 demo/测试” |

## 修复策略（W1~W2）

1. 先处理 `P0`（UF-001/003/004），避免“看起来可用但实际未生效”。
2. `P1` 先做文档与实现对齐（UF-005），确保验收口径一致。
3. `P2` 在版本说明中标注“预留能力”，避免对外误解。

## 验收记录

| ID | 是否完成 | 完成日期 | 验收方式 | 备注 |
|---|---|---|---|---|
| UF-001 | 否 |  |  |  |
| UF-002 | 否 |  |  |  |
| UF-003 | 否 |  |  |  |
| UF-004 | 否 |  |  |  |
| UF-005 | 否 |  |  |  |
| UF-006 | 否 |  |  |  |
