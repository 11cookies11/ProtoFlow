# ProtoFlow v0.4.0（草案）

对比基线：`v0.3.2..HEAD`

## 新增功能
- 事件接入：`RuntimeContext` 支持订阅外部 EventBus 事件队列；变量快照新增 `event_name`、`event_payload`（表达式中可用 `$event_name` / `$event_payload`）。
- Demo 友好：新增 `dummy` 通道类型，适用于无实际串口/TCP 连接的演示脚本。

## 文档与示例
- 新增英文用户指南 `docs/USER_GUIDE_EN.md`。
- 新增 `COMMIT_TEMPLATE.md`（提交模板）与 `VERSION` 文件（当前为 `v0.3.2`，发版时可同步更新）。
