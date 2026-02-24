# W2-UF004 设置项生效矩阵（Runtime / Network / Logs）

## 目标
- 明确每个设置字段当前是“已生效”还是“仅保存”。
- 保证至少一项 COM 主链路设置真实生效，并给出证据路径。

## 字段映射矩阵

| 分组 | UI 字段 | 后端存储 | 运行时消费点 | 当前状态 |
|---|---|---|---|---|
| serial | `defaultBaud` | `settings.serial.defaultBaud` | `App.vue -> applySettings -> baud/channelBaud`，后续连接调用 `connect_serial(_advanced)` | 已生效 |
| serial | `defaultParity` | `settings.serial.defaultParity` | `App.vue -> applySettings -> channelParity`，连接时传入 `connect_serial_advanced(parity)` | 已生效 |
| serial | `defaultStopBits` | `settings.serial.defaultStopBits` | `App.vue -> applySettings -> channelStopBits`，连接时传入 `connect_serial_advanced(stopBits)` | 已生效 |
| network | `tcpTimeoutMs` | `settings.network.tcpTimeoutMs` | `web_bridge._apply_comm_settings -> CommunicationManager.set_network_config` | 已生效 |
| network | `tcpHeartbeatSec` | `settings.network.tcpHeartbeatSec` | 仅保存，无消费点 | 仅保存 |
| network | `tcpRetryCount` | `settings.network.tcpRetryCount` | 仅保存，无消费点 | 仅保存 |
| runtime | `eventQueueSize` | `settings.runtime.eventQueueSize` | 仅保存，无消费点 | 仅保存 |
| runtime | `captureBufferLimit` | `settings.runtime.captureBufferLimit` | 仅保存，无消费点 | 仅保存 |
| runtime | `uiEventRelay` | `settings.runtime.uiEventRelay` | 仅保存，无消费点 | 仅保存 |
| logs | `level` | `settings.logs.level` | 仅保存，无消费点 | 仅保存 |
| logs | `retentionDays` | `settings.logs.retentionDays` | 仅保存，无消费点 | 仅保存 |
| logs | `autoArchive` | `settings.logs.autoArchive` | 仅保存，无消费点 | 仅保存 |
| logs | `includeHex` | `settings.logs.includeHex` | 仅保存，无消费点 | 仅保存 |

## 对齐策略（W2）
- 对 `runtime/logs` 已在 UI 标注“当前用于配置保存，逐步接入”。
- 对 `network` 仅 `tcpTimeoutMs` 标记为已生效，其他字段保留但不承诺本期生效。
- 对 `serial` 默认项，保证连接前默认值会回灌到连接参数（COM 主链路可验证）。

## 验收口径（UF004 Done）
- 有完整参数映射表（本文件）。
- 至少一项 COM 主链路设置可验证生效（本期为 `defaultBaud/defaultParity/defaultStopBits`）。
- 未生效项在 UI 已有提示，不误导为“即时生效”。
