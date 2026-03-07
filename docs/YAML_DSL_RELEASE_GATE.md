# YAML-DSL 发布门禁（v0.2）

日期：2026-03-06

## Gate 1：全量通过率
- 要求：`runtime_regression_suite` 通过率 `100%`。
- 命令：
```powershell
.\.venv\Scripts\python.exe scripts/runtime_regression_suite.py
```

## Gate 2：关键路径零回归
- 关键路径：
  - DSL 核心能力：`yaml_dsl_capability_suite`
  - 组合工况：`yaml_dsl_combo_regression`
  - 故障联动：`yaml_dsl_fault_injection_regression`
  - 协议包契约：`protocol_package_test_suite`
- 要求：以上入口全部 `RESULT: PASSED`。

## Gate 3：基线报告归档
- 要求：保留最近一次稳定与性能基线报告（运行产物）。
- 基线文件：
  - `runs/yaml_dsl_stability_regression_report.json`
  - `runs/yaml_dsl_performance_baseline_report.json`
  - `runs/yaml_dsl_performance_baseline_report.md`

## Gate 4：CI 层级通过
- 要求：
  - `PR Fast Set`（当前变更）通过
  - 最近一次 `Nightly Full Set` 通过
  - 最近一次 `Weekly Soak Set` 通过
- 参考：`docs/YAML_DSL_TEST_CI_TIERS.md`
