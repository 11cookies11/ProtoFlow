# Modbus 三外置包统一规范（v0.1）

## 1. 目标

将 Modbus 能力拆分为三个外置协议包，并保持统一的 `send/recv/rpc` API 与数据模型：

- `modbus_rtu_pkg`
- `modbus_ascii_pkg`
- `modbus_tcp_pkg`

## 2. 统一请求模型（request）

最小字段：

- `op`: 操作类型，支持
  - `read_holding` (FC03)
  - `read_input` (FC04)
  - `write_single_coil` (FC05)
  - `write_single_register` (FC06)
  - `write_multiple_coils` (FC15)
  - `write_multiple_registers` (FC16)
- `unit_id`: 1..247（RTU/ASCII 必填，TCP 可选，默认 1）
- `address`: 起始地址，0..65535
- `quantity`: 读取数量（读操作必填）
- `value`: 单点写值（FC05/FC06）
- `values`: 多点写值数组（FC15/FC16）
- `transaction_id`: TCP 可选，默认自增/或 0
- `timeout_ms`: 可选，覆盖调用超时

## 3. 统一响应模型（response）

成功响应：

- `ok: true`
- `function`: 功能码
- `unit_id`
- `data`:
  - 读：`registers` 或 `coils`
  - 写：`address/quantity/value`
- `raw`: `{ tx_hex, rx_hex }`

失败响应（异常响应或校验失败）：

- `ok: false`
- `error`:
  - `code`: 统一错误码
  - `message`
  - `exception_code`（若为 Modbus 异常响应）
- `raw`（可选）

## 4. 统一错误码

- `MODBUS_TIMEOUT`
- `MODBUS_FRAME_INVALID`
- `MODBUS_CRC_INVALID`
- `MODBUS_LRC_INVALID`
- `MODBUS_MBAP_INVALID`
- `MODBUS_FUNCTION_UNSUPPORTED`
- `MODBUS_EXCEPTION_RESPONSE`
- `MODBUS_VALUE_INVALID`

## 5. 三包边界

### 5.1 modbus_rtu_pkg

- 负责 RTU ADU：`[unit][pdu][crc_lo][crc_hi]`
- 校验 CRC16
- 串口半双工场景

### 5.2 modbus_ascii_pkg

- 负责 ASCII ADU：`':' + HEX + LRC + CRLF`
- 校验 LRC
- 支持 ASCII 十六进制文本编解码

### 5.3 modbus_tcp_pkg

- 负责 TCP ADU：MBAP(7 bytes) + PDU
- 处理 `transaction_id/protocol_id/length/unit_id`
- 不做 CRC/LRC

## 6. 公共层复用范围

三个包复用同一套 PDU 编解码（功能码语义）：

- 请求 PDU 编码
- 正常响应 PDU 解码
- 异常响应解析（`function|0x80` + `exception_code`）

传输层差异（RTU/ASCII/TCP）只在 ADU 封装与校验层处理。
