# YAML-DSL v0.1 发布冻结清单

日期：2026-03-06  
状态：已执行（本次迭代）

## 1. 范围冻结
- [x] 仅覆盖 v0.1 MVP 范围（session/send/expect/sleep/capture/assert/retry/on_fail/artifacts）
- [x] 旧 DSL 语法不纳入本次兼容范围

## 2. 实现项核对
- [x] session 配置解析（serial/eol/encoding/open/read timeout）
- [x] send（text/hex + `${var}` 模板）
- [x] expect（contains/regex/startswith + timeout）
- [x] sleep（ms）
- [x] capture（独立 step + expect 内联）
- [x] assert（expr/match + all/any）
- [x] retry/backoff/on_fail
- [x] params 与 vars 生命周期分离
- [x] artifacts 导出（raw_log/summary/report）

## 3. 验证记录
- [x] 编译检查通过  
  命令：
  `python -m py_compile dsl_runtime/lang/ast_nodes.py dsl_runtime/lang/parser.py dsl_runtime/engine/context.py dsl_runtime/engine/channels.py dsl_runtime/engine/v01_executor.py dsl_runtime/engine/v01_artifacts.py dsl_runtime/engine/runner.py ui/desktop/script_runner_qt.py`
- [x] v0.1 回归脚本通过  
  命令：
  `python scripts/v01_dsl_regression.py`  
  结果：`RESULT: PASSED`

## 4. 文档交付
- [x] 设计基线：`docs/YAML_DSL_DESIGN_BASELINE.md`
- [x] 通道契约：`docs/YAML_DSL_V01_CHANNEL_CONTRACT.md`
- [x] Schema 规范：`docs/YAML_DSL_V01_SCHEMA_SPEC.md`
- [x] 快速开始：`docs/YAML_DSL_V01_QUICKSTART.md`
- [x] 示例脚本：`docs/examples/v01/*.yaml`
