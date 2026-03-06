# Modbus 三外置包使用指南

## 1. 包选择建议

- `modbus_rtu`：串口 RTU 现场设备，低成本主从总线。
- `modbus_ascii`：历史设备或明确要求 ASCII 帧格式的场景。
- `modbus_tcp`：以太网设备、网关转发、上位机集中采集。

## 2. 统一请求模型

三包统一使用：

- `op`: `read_holding|read_input|write_single_coil|write_single_register|write_multiple_coils|write_multiple_registers`
- `unit_id`
- `address`
- `quantity` / `value` / `values`

示例：

```yaml
- name: protocol.rpc
  protocol: modbus_rtu
  request:
    op: read_holding
    unit_id: 1
    address: 0
    quantity: 2
```

## 3. 错误语义

常见错误码：

- `MODBUS_TIMEOUT`
- `MODBUS_CRC_INVALID` / `MODBUS_LRC_INVALID`
- `MODBUS_MBAP_INVALID`
- `MODBUS_EXCEPTION_RESPONSE`
- `MODBUS_VALUE_INVALID`

## 4. 示例脚本

- `scripts/examples/modbus_rtu_flow_v01.yaml`
- `scripts/examples/modbus_ascii_flow_v01.yaml`
- `scripts/examples/modbus_tcp_flow_v01.yaml`

## 5. 向量回归

```powershell
$env:PYTHONPATH='.'
d:\GitRepository\ProtoFlow\.venv\Scripts\python.exe scripts/protocol_vectors_regression.py --root protocols --protocol modbus_rtu
d:\GitRepository\ProtoFlow\.venv\Scripts\python.exe scripts/protocol_vectors_regression.py --root protocols --protocol modbus_ascii
d:\GitRepository\ProtoFlow\.venv\Scripts\python.exe scripts/protocol_vectors_regression.py --root protocols --protocol modbus_tcp
```

## 6. 从旧脚本迁移

1. 把旧的 Modbus 专用 action 改为 `protocol.send/recv/rpc`。
2. 请求参数改为统一 `op/unit_id/address/...` 模型。
3. 补 `expect` 条件并加入 vectors 用例。
4. 跑回归脚本确认行为一致。
