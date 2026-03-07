# YAML-DSL v0.2 发布冻结清单

日期：2026-03-06  
状态：已执行（本次迭代）

## 1. 范围冻结
- [x] v0.2 增量能力冻结：if/loop/parse/path/measure/assert_range/include/template/profile/exec/file/switch_session
- [x] 保持 v0.1 既有能力可用

## 2. 实现核对
- [x] 受控控制流：if/else
- [x] 受控循环：loop(times/until)
- [x] 结构化解析：parse(json/kv/csv)
- [x] 路径取值：path(a.b.c)
- [x] 指标采集：measure
- [x] 阈值断言：assert_range
- [x] 复用机制：imports/include
- [x] 模板机制：step_templates
- [x] 会话复用：profiles + session.profile
- [x] 受控执行：exec（命令白名单 + cwd 白名单）
- [x] 受控文件：file（根目录白名单）
- [x] 会话切换：switch_session（含 dry_run）
- [x] 统一错误码与结构化失败对象
- [x] step 级审计字段（attempts/retry_count/on_fail_steps）

## 3. 验证记录
- [x] 编译检查通过  
命令：  
`python -m py_compile dsl_runtime/lang/ast_nodes.py dsl_runtime/lang/parser.py dsl_runtime/engine/context.py dsl_runtime/engine/channels.py dsl_runtime/engine/v01_executor.py dsl_runtime/engine/v01_artifacts.py dsl_runtime/engine/runner.py ui/desktop/script_runner_qt.py scripts/v01_dsl_regression.py`

- [x] 回归脚本通过  
命令：  
`python scripts/v01_dsl_regression.py`  
结果：`RESULT: PASSED`

## 4. 文档与样例
- [x] v0.2 Schema：`docs/YAML_DSL_V02_SCHEMA_SPEC.md`
- [x] 迁移与最佳实践：`docs/YAML_DSL_V02_MIGRATION_AND_BEST_PRACTICES.md`
- [x] v0.2 示例：`docs/examples/v02/`
