# 外置协议包规范 v0.1

日期：2026-03-06  
状态：Draft-Ready

## 1. 目标
- 软件协议能力统一走外置协议包，不再提供内置协议实现路径。
- 协议包对 YAML-DSL 暴露统一接口：`send` / `recv` / `rpc`。
- 协议包必须可被加载、校验、自测（`vectors.yaml`）。

## 2. 协议包目录契约
每个协议包目录必须包含：

1. `protocol.yaml`
2. `impl.py`
3. `README.md`
4. `vectors.yaml`

推荐目录示例：
```text
protocols/
  modbus_rtu_pkg/
    protocol.yaml
    impl.py
    README.md
    vectors.yaml
```

## 3. protocol.yaml schema
最小字段：
```yaml
id: "modbus_rtu"
name: "Modbus RTU Package"
version: "1.0.0"

entry:
  module: "impl"
  class: "ProtocolPackage"

api:
  - send
  - recv
  - rpc

config_schema: {}
message_schema: {}
```

字段约束：
- `id`: 全局唯一，建议 `snake_case`
- `version`: 语义化版本字符串
- `entry.module`: Python 模块名（相对协议包目录）
- `entry.class`: 实现类名
- `api`: 当前固定包含 `send/recv/rpc`
- `config_schema/message_schema`: 可选，保留扩展

## 4. 统一 Python API 契约
协议包实现类必须提供：

1. `send(ctx, request) -> dict`
2. `recv(ctx, expect) -> dict`
3. `rpc(ctx, request) -> dict`

返回建议：
```python
{
  "ok": True,
  "tx_hex": "...",
  "rx_hex": "...",
  "data": {...},
}
```

异常建议：
- 抛出受控异常或返回 `ok=False`，由网关统一映射错误码。

## 5. ctx 能力边界
`ctx` 提供统一、受控能力：
- `ctx.write(bytes_or_str)`
- `ctx.read(size, timeout_ms)` / `ctx.read_until(...)`
- `ctx.logger`
- `ctx.timeout_ms`
- `ctx.vars_get/vars_set`
- `ctx.artifacts`

不提供任意系统能力（例如直接 shell 调用），保持安全边界。

## 6. vectors.yaml 规范（强烈建议）
每个协议包必须携带 `vectors.yaml`（用于自测与 CI）：
```yaml
version: "1"
protocol_id: "modbus_rtu"

cases:
  - id: "send_basic"
    kind: "send"
    input:
      request: { ... }
    expect:
      ok: true

  - id: "recv_basic"
    kind: "recv"
    input:
      expect: { ... }
    expect:
      ok: true

  - id: "rpc_basic"
    kind: "rpc"
    input:
      request: { ... }
    expect:
      ok: true
```

## 7. YAML-DSL 调用形态（预留）
v0.3 计划新增：
- `protocol.send`
- `protocol.recv`
- `protocol.rpc`

统一参数：
- `protocol_id`
- `request/expect`
- `timeout_ms`
- `save_as`

## 8. 迁移原则
- 禁止新增内置协议实现入口。
- 现有内置协议能力将迁移为外置协议包示例并通过包加载器接入。
