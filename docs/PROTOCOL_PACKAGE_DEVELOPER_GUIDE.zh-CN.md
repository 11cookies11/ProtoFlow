# 外置协议包开发指南（v0.3）

## 1. 目录结构

每个协议包目录必须包含以下文件：

```text
<pkg_dir>/
  protocol.yaml
  impl.py
  README.md
  vectors.yaml
```

## 2. protocol.yaml 最小示例

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
```

约束：
- `id` 全局唯一。
- `entry.module` 相对协议包目录，支持点路径（如 `pkg.impl`）。
- `api` 必须声明 `send/recv/rpc`。

## 3. impl.py 接口

入口类由 `entry.class` 指定，必须实现：

- `send(ctx, request) -> dict`
- `recv(ctx, expect) -> dict`
- `rpc(ctx, request) -> dict`

说明：
- `ctx.channel.write(...)` 发送数据。
- `ctx.channel.read(size, timeout=...)` 接收数据。
- `ctx.timeout_ms` 为调用超时预算。
- 返回值建议为字典，便于 DSL 保存到变量。

## 4. YAML-DSL 调用方式

```yaml
- name: protocol.send
  protocol: modbus_rtu
  request:
    unit: 1
    function: 3
    payload_hex: "00000002"
  timeout_ms: 2000
  save_as: modbus_send_result
```

支持：
- `protocol.send`
- `protocol.recv`
- `protocol.rpc`

## 5. vectors.yaml 自测

`vectors.yaml` 用于协议包自测和 CI 回归：

```yaml
version: "1"
protocol_id: "modbus_rtu"
cases:
  - id: "send_ok"
    kind: "send"
    input:
      request: { unit: 1, function: 3, payload_hex: "00000002" }
    expect:
      ok: true
```

可使用：
- `mock_rx_text`
- `mock_rx_hex`

注入接收数据，验证 `recv/rpc` 路径。

## 6. 回归命令

在仓库根目录执行：

```powershell
$env:PYTHONPATH='.'
d:\GitRepository\ProtoFlow\.venv\Scripts\python.exe scripts/protocol_package_test_suite.py
```

## 7. 错误与审计

网关统一错误码：
- `PROTOCOL_NOT_FOUND`
- `PROTOCOL_METHOD_INVALID`
- `PROTOCOL_METHOD_UNDECLARED`
- `PROTOCOL_METHOD_UNSUPPORTED`
- `PROTOCOL_TIMEOUT`
- `PROTOCOL_VALIDATION_FAILED`
- `PROTOCOL_PERMISSION_DENIED`
- `PROTOCOL_CALL_FAILED`

网关统一审计日志事件：
- `call_start`
- `call_end`
