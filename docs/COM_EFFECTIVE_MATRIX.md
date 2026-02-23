# COM 参数生效矩阵（当前代码基线）

## 说明

- 范围：仅关注 COM/Serial 主链路（不含 TCP 新功能）。
- 结论标签：
  - `effective`：参数已被底层通信代码消费并影响行为。
  - `ui-only`：参数仅存在于 UI/配置保存，未进入底层通信。
  - `partial`：部分路径生效，仍有缺口。

## 参数矩阵

| 参数 | UI来源 | 后端入口 | 底层消费点 | 当前状态 | 证据 |
|---|---|---|---|---|---|
| `port` | 通道弹窗 / 手动连接 | `bridge.connect_serial(port, baud)` | `serial.Serial(port=...)` | effective | `ui/frontend/src/App.vue:3832`, `ui/desktop/web_bridge.py:429`, `infra/comm/serial_manager.py:50` |
| `baud` / `defaultBaud` | 通道弹窗 / 设置页默认值 | `bridge.connect_serial(port, baud)` | `serial.Serial(baudrate=...)` | effective | `ui/frontend/src/App.vue:3805`, `ui/frontend/src/App.vue:3832`, `infra/comm/serial_manager.py:50` |
| `defaultParity` | 设置页 | 快速连接与弹窗连接路径 | `serial.Serial(parity=...)` | effective | `ui/frontend/src/App.vue:4527`, `ui/frontend/src/App.vue:3850`, `ui/desktop/web_bridge.py:446` |
| `defaultStopBits` | 设置页 | 快速连接与弹窗连接路径 | `serial.Serial(stopbits=...)` | effective | `ui/frontend/src/App.vue:4528`, `ui/frontend/src/App.vue:3851`, `ui/desktop/web_bridge.py:447` |
| `channelDataBits` | 通道弹窗 | `connect_serial_advanced` | `serial.Serial(bytesize=...)` | effective | `ui/frontend/src/App.vue:5102`, `ui/desktop/web_bridge.py:445`, `infra/comm/serial_manager.py:62` |
| `channelParity` | 通道弹窗 | `connect_serial_advanced` | `serial.Serial(parity=...)` | effective | `ui/frontend/src/App.vue:5113`, `ui/desktop/web_bridge.py:446`, `infra/comm/serial_manager.py:63` |
| `channelStopBits` | 通道弹窗 | `connect_serial_advanced` | `serial.Serial(stopbits=...)` | effective | `ui/frontend/src/App.vue:5106`, `ui/desktop/web_bridge.py:447`, `infra/comm/serial_manager.py:64` |
| `channelFlowControl` | 通道弹窗 | `connect_serial_advanced` | `serial.Serial(rtscts/xonxoff=...)` | effective | `ui/frontend/src/App.vue:5124`, `ui/desktop/web_bridge.py:448`, `infra/comm/serial_manager.py:67` |
| `channelReadTimeout` | 通道弹窗 | `connect_serial_advanced` | `serial.Serial(timeout=...)` | effective | `ui/frontend/src/App.vue:5134`, `ui/desktop/web_bridge.py:449`, `infra/comm/serial_manager.py:65` |
| `channelWriteTimeout` | 通道弹窗 | `connect_serial_advanced` | `serial.Serial(write_timeout=...)` | effective | `ui/frontend/src/App.vue:5138`, `ui/desktop/web_bridge.py:450`, `infra/comm/serial_manager.py:66` |
| 自动重连（隐式） | 底层机制 | `SerialManager._attempt_reconnect` | `serial.Serial(...)` 重建连接 | effective | `infra/comm/serial_manager.py:114`, `infra/comm/serial_manager.py:132` |

## 关键结论

1. 当前 COM 主链路已生效参数：`port`、`baud`、`dataBits`、`parity`、`stopBits`、`flowControl`、`readTimeout`、`writeTimeout`。
2. `defaultParity/defaultStopBits` 已在“手动快速连接 + 通道弹窗连接”两条路径生效。
3. 自动重连机制已存在并生效，且会复用当前串口高级参数配置。

## 建议实施顺序（COM 优先）

1. 补齐手动快速连接路径对高级参数的消费（与通道弹窗路径统一）。
2. 增加“当前连接参数”可视化（便于定位配置是否生效）。
3. 针对 `flowControl` 增加设备兼容测试与异常提示。

## 建议验收用例（最小集）

1. 使用 `7E1` 设备验证 `dataBits/parity/stopBits` 生效（错误配置应连接或通信失败，正确配置应恢复）。
2. 设置极短 `readTimeout` 并验证超时行为变化。
3. 设置 `flowControl=RTS/CTS` 与 `none` 对比链路行为（若设备支持）。
