# 发布冻结清单：协议包扩展 v0.4（AT/YMODEM/SCPI）

日期：2026-03-06  
范围：`9dbfb22` -> 当前 `HEAD`

## 1. 冻结目标

- 完成 `at_command` / `ymodem` / `scpi` 三外置协议包。
- 完成三包 vectors、示例脚本与统一回归接入。

## 2. 功能核对

- [x] `at_command_pkg`：多行回显、OK/ERROR、超时、expect 断言
- [x] `ymodem_pkg`：握手、分包、重传、EOT 收尾
- [x] `scpi_pkg`：write/query、多行响应、CSV 解析
- [x] 三包均具备 `protocol.yaml/impl.py/README.md/vectors.yaml`
- [x] 三包 YAML-DSL 示例脚本已提供
- [x] 统一回归套件已接入三包

## 3. 回归结果

执行环境：`d:\GitRepository\ProtoFlow\.venv\Scripts\python.exe`，`PYTHONPATH=.`

1. `scripts/protocol_vectors_regression.py --root protocols --protocol at_command`
- 结果：PASS（8/8）

2. `scripts/protocol_vectors_regression.py --root protocols --protocol ymodem`
- 结果：PASS（8/8）

3. `scripts/protocol_vectors_regression.py --root protocols --protocol scpi`
- 结果：PASS（8/8）

4. `scripts/protocol_package_test_suite.py`
- 结果：PASS

## 4. 结论

协议包扩展 v0.4（AT/YMODEM/SCPI）达到发布冻结条件。
