# W5-03 脚本运行可观测性说明

## 新增生命周期日志

`ui/desktop/script_runner_qt.py` 在脚本执行过程中统一输出以下日志：

- `[LIFECYCLE] script.start`
- `[LIFECYCLE] script.finished elapsed_ms=<...> visited=<...> progress=<...>`
- `[LIFECYCLE] script.stopped elapsed_ms=<...> visited=<...> progress=<...>`
- `[LIFECYCLE] script.failed elapsed_ms=<...> error=<...>`

## 目的

- 将“启动/停止/完成/失败”状态以统一格式暴露给 UI 日志面板。
- 便于定位脚本执行时长、状态推进数量和停止时机。

## 关联门禁

- 生命周期闭环门禁：`scripts/dsl_lifecycle_gate.py`
