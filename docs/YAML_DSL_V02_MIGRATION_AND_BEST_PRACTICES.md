# YAML-DSL v0.2 迁移说明与最佳实践

日期：2026-03-06

## 1. 版本定位
- v0.1：最小可用（send/expect/sleep/capture/assert/retry/artifacts）
- v0.2：可用性增强（控制流、解析、指标、复用、受控 exec/file、switch_session）

## 2. v0.1 -> v0.2 迁移
1. 版本号升级为 `version: "0.2"`。
2. 若需要复用会话配置，新增 `profiles` 并在 `session.profile` 引用。
3. 若要复用步骤，新增 `step_templates`，通过 `template + args` 调用。
4. 若有多脚本拆分，使用 `imports/include` 合并外部步骤片段。
5. 使用 `security.exec` / `security.file` 明确白名单策略后再启用相关 step。

## 3. 推荐写法
1. 控制流优先用 `if` + `loop`，避免无边界跳转。
2. `parse -> path -> measure -> assert_range` 作为产测标准链路。
3. `retry` 仅用于可恢复步骤（通信超时、瞬态响应失败），不要用于配置错误。
4. 统一在 `artifacts.dir` 使用 `${now}`，避免多次运行覆盖。
5. 所有关键步骤都写 `id`，便于 summary 定位失败点。

## 4. 安全建议
1. `exec` 必须配置 `allow_commands` 与 `cwd_allowlist`。
2. `file` 必须配置 `root_allowlist`，避免越权读写。
3. 不要在日志中直接打印密钥、证书、密码。

## 5. 常见问题
1. `STEP_TIMEOUT`：增大 step `timeout_ms` 或优化设备响应窗口。
2. `ASSERT_FAILED`：检查 capture/path 是否写入预期变量。
3. `EXEC_NOT_ALLOWED` / `FILE_NOT_ALLOWED`：补齐 security 白名单。
4. `STEP_NOT_IMPLEMENTED`：脚本使用了当前执行器未支持的 step。

## 6. 与文档对应关系
- Schema：`docs/YAML_DSL_V02_SCHEMA_SPEC.md`
- 示例：`docs/examples/v02/`
- 回归脚本：`scripts/v01_dsl_regression.py`
