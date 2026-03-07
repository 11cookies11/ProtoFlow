# 协议包扩展指南（v0.4）

## 1. 本阶段范围

v0.4 聚焦三类高价值协议包：

- `at_command`：模块调试与配置
- `ymodem`：固件传输与升级流程
- `scpi`：仪器控制与数据采集

## 2. 选型建议

### 2.1 at_command

适用：
- Wi-Fi/4G/BT/GNSS 模块调试
- 现场参数配置与日志开关

能力：
- 多行回显解析
- `OK/ERROR` 终态判定
- `contains/regex/status` 断言

### 2.2 ymodem

适用：
- Boot/升级窗口内文件下发
- 需要重传与握手可靠性的串口升级

能力：
- `C` 握手
- 头包/数据包/EOT 收尾
- `NAK` 重传
- 超时与取消处理

### 2.3 scpi

适用：
- 电源/示波器/信号源/万用表自动化
- 产测数据采集

能力：
- write/query
- 多行响应处理
- CSV 标量解析（value/unit/raw）

## 3. 示例脚本

- `scripts/examples/at_command_flow_v01.yaml`
- `scripts/examples/ymodem_flow_v01.yaml`
- `scripts/examples/scpi_flow_v01.yaml`

## 4. 回归与验证

统一回归入口：

```powershell
$env:PYTHONPATH='.'
d:\GitRepository\ProtoFlow\.venv\Scripts\python.exe scripts/protocol_package_test_suite.py
```

单包向量回归：

```powershell
$env:PYTHONPATH='.'
d:\GitRepository\ProtoFlow\.venv\Scripts\python.exe scripts/protocol_vectors_regression.py --root protocols --protocol at_command
d:\GitRepository\ProtoFlow\.venv\Scripts\python.exe scripts/protocol_vectors_regression.py --root protocols --protocol ymodem
d:\GitRepository\ProtoFlow\.venv\Scripts\python.exe scripts/protocol_vectors_regression.py --root protocols --protocol scpi
```

## 5. 从旧流程迁移

1. 把旧 action 改为 `protocol.send/recv/rpc`。
2. 迁移到外置协议包请求模型。
3. 为关键流程补 vectors 用例。
4. 用 `protocol_package_test_suite.py` 做回归门禁。
