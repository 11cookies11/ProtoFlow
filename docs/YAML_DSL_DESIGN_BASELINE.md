# YAML DSL 设计基线（MVP / v1 / v2）

日期：2026-03-06  
状态：已固化（设计输入）

## 必须有（MVP：覆盖 70%+ COM 用例）

### 1) 连接与会话（Session）
- `transport`: `serial` + `port` / `baud` / `data_bits` / `parity` / `stop_bits`
- `eol`（CR/LF/CRLF）与编码（ASCII/HEX）
- `open` / `close`，以及动态切换波特率/端口（升级/boot 常见）

### 2) 基本动作 Step（Action primitives）
- `send`：发送字符串/HEX（支持模板变量）
- `expect`：等待回显（关键字/正则），带 `timeout`
- `sleep`：延时（boot 窗口常用）

说明：`send + expect + sleep` 配合控制逻辑，可覆盖升级、参数写入、诊断主流程。

### 3) 匹配与抓取（Match & Capture）
- `match`：`contains` / `regex` / `startswith`
- `capture`：从回显用 regex 提取字段写入变量（版本号、SN、错误码、温度、电压等）

### 4) 可靠性（Reliability）
- `timeout_ms`
- `retry: { count, backoff_ms }`（指数退避可选）
- `on_fail`：失败后的步骤（reset / 重试 / 回收日志）
- `assert`：断言成功条件（文本匹配或变量条件）

### 5) 变量与参数化（Variables）
- `params`：运行前输入（端口、固件路径、SN、阈值）
- `vars`：运行中变量（来自 capture）
- 模板：固定为一种风格（`{{var}}` 或 `${var}`）
- 基本表达式：比较 / 字符串拼接 / 数值转换（以够用为目标）

### 6) 日志与输出产物（Artifacts）
- 自动记录：每步开始/结束、发送、接收、耗时
- 可导出：`raw_log`, `summary.json`, `report.csv`（至少支持一种）

## 强烈建议（v1：覆盖产测/回归/多分支）

### 7) 控制流（Controlled flow，避免脚本化）
- `if / else`（基于变量或匹配结果）
- `switch`（基于错误码/状态）
- `loop`（次数循环或 until）
- `goto`（可选，谨慎）

建议优先结构化写法：`when + retry/until`，降低流程失控风险。

### 8) 结构化解析（不止 regex）
- `parse: json|kv|csv` 输出字典
- 支持路径取值（如 `path: a.b.c`）

### 9) 数据点与阈值断言（产测导向）
- `measure`：记录指标（电压/温度/转速）
- `assert_range`：`min/max`、`abs_err`、`in_set`

### 10) Step 复用与模块化
- `include/import`：通用流程库（如 `enter_boot`、`flash`、`read_version`）
- `step_templates`：参数化步骤模板
- `profile`：串口配置复用（不同板型）

### 11) 外部命令与文件（受控）
- `exec`：调用外部命令（烧录器、解包、校验）
- `file`：读写文件（日志/CSV）

约束：限制 `exec` 输入输出边界（仅 stdout/stderr 等），避免 DSL 演化为任意脚本平台。

## 可选高级（v2：产线/多设备/复杂协议）

### 12) 多设备/并发模型
- `devices`：多个串口会话
- `run: parallel|serial`，并发上限与资源锁

### 13) 专用传输协议 Step
- `xmodem_send` / `ymodem_send`
- `chunk_send`（自定义分包 + ack/seq/crc）
- `progress`（进度事件）

### 14) 事件驱动（流式触发）
- `watch`：持续监听输出
- `on_event`：匹配后触发动作（例如 PANIC 立即抓日志并停止）

### 15) 安全与审计（密钥/证书场景）
- 参数加密 / 日志脱敏
- 权限策略（限制可执行 step）
- 审计记录（谁在何时写入了什么）

## 推荐核心抽象（设计约束）
为同时支持升级 / 写入 / 产测 / 诊断，DSL 固定四层：

1. `Profile / Session`：怎么连（串口参数、换行、默认超时）
2. `Steps`：做什么（`send/expect/parse/assert/transfer/exec`）
3. `Flow control`：何时做（`if/loop/retry/on_fail`）
4. `Artifacts`：产出什么（日志/报告/指标）
