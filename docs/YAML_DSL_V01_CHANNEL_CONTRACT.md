# YAML-DSL v0.1 通道契约（Channel Contract）

日期：2026-03-06  
状态：v0.1 设计基线

## 1. 目标
- 在“直接替代旧语法”的前提下，确保串口会话行为可预测、可恢复、可审计。
- 为 `session/steps/flow/artifacts` 提供稳定的底层通道语义。

## 2. 关键对象

### 2.1 `IChannelSession`
统一通道会话接口（v0.1 先覆盖 serial）：
- `open(config) -> SessionHandle`
- `close(handle) -> None`
- `switch(handle, config) -> SessionHandle`（原子重连）
- `write_text(handle, text, eol, encoding) -> TxResult`
- `write_hex(handle, hex_bytes) -> TxResult`
- `read_until(handle, matcher, timeout_ms) -> RxResult`
- `drain(handle, timeout_ms) -> DrainResult`
- `get_status(handle) -> SessionStatus`

### 2.2 `SessionManager`
- 管理会话租约与串口独占。
- 处理步骤层请求到具体 session 的路由。
- 负责连接状态转换和资源回收。

## 3. 会话状态机
- `closed`：无会话
- `opening`：建立连接中
- `active`：可收发
- `switching`：切端口/波特率中（必须阻断并发收发）
- `closing`：释放中
- `error`：故障态（可由 flow 决定 retry/on_fail）

状态转换要求：
- `switch` 必须按 `close(old) -> open(new)` 执行。
- 切换失败时返回明确错误，不允许“半开连接”。

## 4. 独占与并发规则
- 同一物理串口同一时刻仅允许一个活动 `SessionHandle`。
- UI 手工串口会话与 DSL 运行会话互斥。
- 当会话被占用，必须返回 `PORT_BUSY`，禁止隐式抢占。

## 5. 编码与换行策略
- `encoding`: `ascii | utf8 | hex`
- `eol`: `none | cr | lf | crlf`
- `send` 行为：
  - `text` 模式：模板展开后按 encoding 编码并附加 eol。
  - `hex` 模式：按字节发送，不附加 eol。
- `expect` 行为：
  - 匹配输入以接收缓冲区文本视图进行（保留原始字节用于 artifacts）。

## 6. 缓冲策略（BufferPolicy）
- 每个 step 执行前可选 `drain_before`（默认 false）。
- 每个 `expect` 在超时前持续消费输入缓冲。
- 匹配命中后可配置 `consume_on_match`（v0.1 默认 true）。
- 所有原始 RX/TX 保留到 `raw_log`，用于复盘。

## 7. 超时模型（统一 `timeout_ms`）
- `open_timeout_ms`：连接建立超时
- `read_timeout_ms`：底层读超时（单次）
- `step_timeout_ms`：步骤级超时（expect/retry 用）
- `session_idle_timeout_ms`：可选，长期空闲自动关闭（v0.1 可不启用）

## 8. 错误码约定（ErrorCode）
- `OPEN_FAILED`
- `CLOSE_FAILED`
- `PORT_BUSY`
- `SWITCH_FAILED`
- `WRITE_FAILED`
- `READ_TIMEOUT`
- `MATCH_FAILED`
- `CAPTURE_FAILED`
- `ASSERT_FAILED`
- `UNEXPECTED_EXCEPTION`

约束：
- 所有错误必须带 `code + message + step_id + ts`。
- `retry/on_fail` 仅基于标准错误码决策，避免字符串判断。

## 9. 日志与审计字段
每个 step 至少记录：
- `step_id`
- `action`
- `started_at` / `ended_at` / `elapsed_ms`
- `tx_text` / `tx_hex`
- `rx_text` / `rx_hex`
- `match_result`
- `error_code` / `error_message`

产物最低要求：
- `raw_log`（逐条）
- `summary.json`（成功/失败、步骤统计、最终变量快照）

## 10. 实施注意事项（替代旧语法）
- 旧 DSL 不做兼容层，入口直接切换到新 schema。
- 先落地契约再改 parser/executor，避免行为发散。
- 先补会话互斥与错误码回归，再接入 `send/expect/sleep`。
