# 发布冻结清单：全外置协议包（v0.3）

日期：2026-03-06  
范围：`4dae11f` -> `554691a`

## 1. 冻结目标

- 协议能力统一走外置协议包。
- YAML-DSL 已支持 `protocol.send/protocol.recv/protocol.rpc`。
- 旧内置协议入口已下线。

## 2. 功能冻结核对

- [x] 协议包目录契约：`protocol.yaml/impl.py/README.md/vectors.yaml`
- [x] 协议包扫描与校验
- [x] 协议包动态加载与注册
- [x] 协议调用网关（统一 dispatch + 错误码 + 审计）
- [x] DSL 协议 step 接入
- [x] 旧内置协议调用路径移除
- [x] vectors 执行器与回归入口
- [x] 外置示例包（modbus_rtu/xmodem）
- [x] 前端协议列表与调用桥接改为外置包
- [x] 自动化测试套件（加载/调用/异常/向量回归）
- [x] 开发/模板/迁移文档

## 3. 回归结果

执行环境：`d:\GitRepository\ProtoFlow\.venv\Scripts\python.exe`，`PYTHONPATH=.`

1. `scripts/protocol_package_test_suite.py`
- 结果：PASS

2. `scripts/protocol_vectors_regression.py --root protocols --protocol modbus_rtu`
- 结果：PASS（3/3）

3. `scripts/protocol_vectors_regression.py --root protocols --protocol xmodem`
- 结果：PASS（3/3）

## 4. 关键提交

- `13053ef` loader + gateway
- `f28da5b` DSL 协议 step
- `ff3b32e` 下线旧协议 action 注册
- `05c81f5` vectors 执行器
- `a71636b` modbus/xmodem 外置示例包
- `370353c` 前端桥接外置化
- `1f34b4c` 网关错误码与审计
- `9950abc` 自动化测试套件
- `554691a` 文档完善

## 5. 结论

本次范围内功能与回归通过，达到“全外置协议包”发布冻结条件。
