# P0 回归用例（可复现步骤 + 预期）

## Case 1: 代理创建与参数校验

- 前置：进入“代理监控”页面
- 步骤：
  1. 新建代理，主机端口留空
  2. 点击保存
  3. 主机端口与设备端口设置为同一个端口
  4. 点击保存
- 预期：
  - 第 1 步保存失败并提示“请选择主机端口和设备端口”
  - 第 3 步保存失败并提示“主机端口和设备端口不能相同”

## Case 2: 代理启动/停止闭环

- 前置：存在一个合法代理对
- 步骤：
  1. 点击代理开关启动
  2. 观察卡片状态
  3. 点击代理开关停止
- 预期：
  - 启动后状态变为 `running`
  - 停止后状态变为 `stopped`
  - 重启应用后状态按 `desiredActive` 恢复一致

## Case 3: 异常可视化与重试

- 前置：人为制造端口占用冲突
- 步骤：
  1. 启动冲突代理
  2. 观察卡片状态与错误提示
  3. 释放冲突后点击“重试”
- 预期：
  - 状态为 `error`
  - 卡片显示错误文本
  - 重试后可恢复 `running`

## Case 4: 抓包方向与通道语义

- 前置：代理处于 `running`
- 步骤：
  1. 打开抓包
  2. 从 host 侧发送数据
  3. 从 device 侧发送数据
- 预期：
  - host->device 映射为 `TX`
  - device->host 映射为 `RX`
  - `channel` 语义稳定，不随来源抖动

## Case 5: Mock 回归（无驱动）

- 前置：`.venv` 可用
- 步骤：
  1. 运行 `.\scripts\run_proxy_regression.ps1 -Mode mock`
  2. 运行 `.\scripts\run_proxy_regression.ps1 -Mode mock -Iterations 50 -SoakSec 60 -InjectDisconnect`
- 预期：
  - 输出 `RESULT: PASSED`
  - 包含 `start_pair / host_to_device / device_to_host / proxy.data_event / status.stopped` 均为 PASS
  - 增强回归包含 `soak.forwarding` 与 `fault.disconnect_error_event` 且均为 PASS

## Case 6: 虚拟串口/真实设备回归

- 前置：端口已准备好（com0com 或真实硬件）
- 步骤：
  1. 运行：
     `.\scripts\run_proxy_regression.ps1 -Mode real -HostPort COM11 -DevicePort COM13 -TestHostPort COM12 -TestDevicePort COM14`
  2. 查看终端与 JSON 报告
- 预期：
  - `RESULT: PASSED`
  - 子项 `status.running / host_to_device.forward / device_to_host.forward` 均 PASS
  - `soak.forwarding` 在启用时 PASS

## Case 7: 退出清理一致性

- 前置：至少一个代理处于 `running`
- 步骤：
  1. 关闭应用
  2. 重启应用并观察代理状态
- 预期：
  - 上次会话不会残留为僵尸占用
  - 状态恢复逻辑一致，不出现“显示运行但实际不可用”

## Case 8: comm 事件序列一致性（Mock）

- 前置：`.venv` 可用
- 步骤：
  1. 运行 `.\.venv\Scripts\python.exe scripts\comm_manager_regression_mock.py`
- 预期：
  - 输出 `RESULT: PASSED`
  - 子项 `serial_connected / serial_disconnected / tcp_connected / tcp_disconnected` 全部 PASS

## Case 9: 协议解析异常提示（Mock）

- 前置：`.venv` 可用
- 步骤：
  1. 运行 `.\.venv\Scripts\python.exe scripts\packet_engine_regression.py`
- 预期：
  - 输出 `RESULT: PASSED`
  - 覆盖以下判定：
    - 正常 Modbus 帧：无错误
    - CRC 错误帧：包含 `CRC_INVALID`
    - 短帧：包含 `FRAME_TOO_SHORT`
    - 异常帧长度不符：包含 `LENGTH_INVALID`

## Case 10: DSL 运行生命周期回归（Mock）

- 前置：`.venv` 可用
- 步骤：
  1. 运行 `.\.venv\Scripts\python.exe scripts\script_runner_regression.py`
- 预期：
  - 输出 `RESULT: PASSED`
  - 正常执行路径包含 `__running__` 与 `__finished__`
  - 停止路径包含 `__stopped__`
  - 异常路径包含 `__error__`
