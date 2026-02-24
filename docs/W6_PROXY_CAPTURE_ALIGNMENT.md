# W6-02 Proxy/Capture 状态对齐说明

## 状态语义

- `running`
  - 含义：真实实时转发链路运行中。
  - 条件：`capability == realtime-forward` 且启用。
- `configured`
  - 含义：仅配置态启用（无实时转发链路）。
  - 条件：`capability == config-only` 且启用。
- `stopped`
  - 含义：未启用。
- `error`
  - 含义：运行异常。

## 对齐改动

- 后端 `web_bridge.set_proxy_pair_status`：
  - `config-only` 启用时写入 `configured`，不再写 `running`。
- 前端 `ProxyMonitorView`：
  - 新增 `configured` 展示分支与筛选项。
  - `running` 筛选兼容显示 `running + configured`（便于操作习惯延续）。
- Capture 状态透传：
  - `PacketAnalysisEngine` 在 `capture.control start/stop` 时发布 `capture.status`。
  - `WebBridge` 转发 `capture_status` 信号，前端据此更新引擎状态显示（运行中/已停止）。

## 目的

- 避免把“仅配置态”误表述为“实时转发中”。
- 保持 Proxy 与 Capture 展示语义与后端能力一致。
