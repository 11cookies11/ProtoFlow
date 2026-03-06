# 迁移说明：从内置协议到全外置协议包

## 背景

从 v0.3 起，协议能力统一收敛为“外置协议包”，不再保留内置协议注册入口。

## 变化点

1. 协议列表来源
- 旧：内置 `ProtocolRegistry` + 自定义协议配置。
- 新：扫描 `protocols/` 目录中的外置协议包。

2. 运行时调用路径
- 旧：内置 action（如 `dsl_protocol_actions` / `dsl_protocol_schema_actions`）。
- 新：`ProtocolPackageGateway` 统一分发 `send/recv/rpc`。

3. DSL 调用方式
- 旧：各类专用 action 分散调用。
- 新：统一 `protocol.send / protocol.recv / protocol.rpc`。

## 迁移步骤

1. 将原协议实现迁移到外置包目录：
- `protocol.yaml`
- `impl.py`
- `README.md`
- `vectors.yaml`

2. 在脚本中改写协议步骤为：
- `name: protocol.send`
- `name: protocol.recv`
- `name: protocol.rpc`

3. 运行回归：

```powershell
$env:PYTHONPATH='.'
d:\GitRepository\ProtoFlow\.venv\Scripts\python.exe scripts/protocol_package_test_suite.py
```

## 兼容性说明

- 已移除旧内置协议 action 注册路径。
- 需要继续运行旧脚本时，请先完成 DSL 步骤迁移。
