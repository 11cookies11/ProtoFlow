# 发布冻结清单：Modbus 三外置包

日期：2026-03-06  
范围：`ca763a5` -> 当前 `HEAD`

## 1. 冻结目标

- 完成 `modbus_rtu` / `modbus_ascii` / `modbus_tcp` 三外置包全功能实现。
- 统一请求模型与错误语义。
- 完成三包向量矩阵回归与 DSL 示例。

## 2. 功能核对

- [x] 三包目录契约齐全（protocol.yaml/impl.py/README.md/vectors.yaml）
- [x] RTU：CRC16 + FC03/04/05/06/15/16 + 异常响应
- [x] ASCII：LRC + FC03/04/05/06/15/16 + 异常响应
- [x] TCP：MBAP + FC03/04/05/06/15/16 + 异常响应
- [x] 公共 PDU 编解码复用
- [x] 向量矩阵：正常/异常码/超时/校验失败/边界值
- [x] 前端分类展示：modbus-rtu/modbus-ascii/modbus-tcp
- [x] 示例脚本：RTU/ASCII/TCP

## 3. 回归结果

执行环境：`d:\GitRepository\ProtoFlow\.venv\Scripts\python.exe`，`PYTHONPATH=.`

1. `scripts/protocol_package_test_suite.py`
- 结果：PASS

2. `scripts/protocol_vectors_regression.py --root protocols --protocol modbus_rtu`
- 结果：PASS（8/8）

3. `scripts/protocol_vectors_regression.py --root protocols --protocol modbus_ascii`
- 结果：PASS（8/8）

4. `scripts/protocol_vectors_regression.py --root protocols --protocol modbus_tcp`
- 结果：PASS（8/8）

## 4. 结论

Modbus 三外置包达到发布冻结条件，可进入后续联调或版本发布阶段。
