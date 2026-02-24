# W5-01 DSL 生命周期门禁说明

## 目标

- 验证 DSL 生命周期闭环：
  - 运行完成（state/progress 能闭环）
  - 停止中断（stop 请求可生效）

## 脚本

- `scripts/dsl_lifecycle_gate.py`

## 执行

```powershell
python scripts/dsl_lifecycle_gate.py
```

## 通过标准

- `passed = true`
- `run_complete` 场景：
  - 最终状态轨迹到达 `done`
  - 进度轨迹最终达到 `100`
- `stop_early` 场景：
  - 停止请求后执行线程可退出
  - 状态轨迹不应到达 `done`

## 说明

- 本门禁使用 `DummyChannel`，不依赖真实串口硬件。
- 门禁用于验证生命周期机制，不替代业务脚本回归。
