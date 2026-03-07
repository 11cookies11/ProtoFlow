# YAML-DSL 测试文档冻结（2026-03-06）

本次冻结包含以下文档：

1. 测试矩阵
- `docs/YAML_DSL_PROTOCOL_TEST_MATRIX.md`

2. 故障注入指南
- `docs/TARGET_EMULATOR_GUIDE.md`
- `tools/target_emulator/scenarios/fault_injection_matrix.yaml`

3. 排障与执行约定
- `docs/YAML_DSL_PROTOCOL_TEST_CONVENTIONS.md`
- `docs/YAML_DSL_TEST_CI_TIERS.md`

4. 发布门禁
- `docs/YAML_DSL_RELEASE_GATE.md`

5. 已知限制
- `expect.retry` 仅重试等待，不自动重发上一条 `send`。
- 靶机场景响应为规则配置值，不提供动态变量回写。
- 长稳/性能报告默认写入 `runs/`，不纳入版本库跟踪。
