# W5-02 协议回放门禁说明

## 目标

- 校验协议解析链路在 Modbus RTU 主路径上的稳定性。
- 验证未知报文不会误识别为 Modbus。
- 验证异常响应（function + 0x80）能在摘要中标识。

## 脚本

- `scripts/protocol_replay_gate.py`

## 执行

```powershell
python scripts/protocol_replay_gate.py
```

## 通过标准

- `passed = true`
- `modbus_frames >= 3`
- `unknown_frames >= 1`
- `exception_frames >= 1`

## 说明

- 该门禁使用内置样例帧，不依赖真实硬件。
- 适用于 W5-02 的快速回归与增强验证。
