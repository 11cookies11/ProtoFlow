# YAML-DSL CI 分层策略

日期：2026-03-06

## 分层定义
1. `PR Fast Set`
- 触发：`pull_request`、`push(main)`、手动 `tier=fast`
- 目标：快速发现 DSL/协议包/靶机主链路回归
- 入口：
  - `scripts/v01_dsl_regression.py`
  - `scripts/target_emulator_regression.py`
  - `scripts/protocol_package_test_suite.py`
  - `scripts/yaml_dsl_capability_suite.py`
  - `scripts/yaml_dsl_combo_regression.py`
  - `scripts/yaml_dsl_fault_injection_regression.py`

2. `Nightly Full Set`
- 触发：每日 `02:20 UTC`、手动 `tier=full`
- 目标：执行全量总回归入口，覆盖 DSL + 协议包 + 靶机 + 长稳/性能基础版
- 入口：
  - `scripts/runtime_regression_suite.py`

3. `Weekly Soak Set`
- 触发：每周日 `03:40 UTC`、手动 `tier=soak`
- 目标：拉高迭代强度进行稳定性与性能基线漂移检查
- 入口：
  - `scripts/yaml_dsl_stability_regression.py --iterations 80 --mem-delta-kb-max 12288`
  - `scripts/yaml_dsl_performance_baseline.py --basic-iters 30 --retry-iters 20`

## 工作流文件
- `.github/workflows/yaml-dsl-regression.yml`

## 判定原则
- 任一层失败即视为该层门禁不通过。
- 发布前必须至少满足：
  - 最近一次 `Nightly Full Set` 通过；
  - 最近一次 `Weekly Soak Set` 通过；
  - 当前分支 `PR Fast Set` 通过。
