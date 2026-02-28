# 代理转发回归（6.1）

本回归用于验证代理监控在真实设备或虚拟串口环境中的稳定性，覆盖：
- 双向转发正确性（host->device / device->host）
- 事件一致性（`proxy.data`、`proxy.status`）
- 长时运行稳定性（可选 soak）

## 1. 环境准备

建议两种方式任选其一：

1. 虚拟串口对（推荐先做）
   - 例如使用 com0com 创建两对端口：
     - PairA: `COM11 <-> COM12`
     - PairB: `COM13 <-> COM14`
   - 应用代理占用 `COM11`、`COM13`
   - 回归脚本占用 `COM12`、`COM14`
2. 真实硬件
   - 两个 USB-Serial 设备交叉连接 TX/RX、共地
   - 确保没有其它工具占用相关端口

## 2. 运行命令

在仓库根目录执行：

```powershell
python scripts/proxy_regression.py `
  --host-port COM11 `
  --device-port COM13 `
  --test-host-port COM12 `
  --test-device-port COM14 `
  --baud 115200 `
  --iterations 30 `
  --payload-size 64 `
  --timeout-sec 2 `
  --soak-sec 180 `
  --json-out .\\proxy_regression_report.json
```

如果当前终端没有 `python` 命令，请改为你的 Python 可执行路径。

### 2.1 环境检查（一键）

可先运行：

```powershell
.\scripts\setup_proxy_test_env.ps1
```

该脚本会检查：
- `.venv` Python 是否存在
- `pyserial` 是否可用
- `com0com` 驱动注册表是否可见
- 当前可见串口列表

### 2.2 无驱动模拟回归（可先执行）

如果本机暂时无法安装虚拟串口驱动，可先运行纯 Python 模拟回归：

```powershell
.\.venv\Scripts\python.exe scripts\proxy_regression_mock.py
```

该脚本不依赖 `com0com`，会在进程内模拟 2 对串口并验证：
- 代理双向转发
- `proxy.data` 事件产出
- `proxy.status` 停止状态事件

## 3. 结果判定

脚本会输出每个子用例 `PASS/FAIL`，并附带延迟统计：
- `status.running`
- `host_to_device.forward`
- `device_to_host.forward`
- `soak.forwarding`（仅在 `--soak-sec > 0` 时）

最终状态：
- `RESULT: PASSED` 表示本轮通过
- `RESULT: FAILED` 表示存在回归风险，需要排查端口映射、占用、参数一致性

同时会输出 JSON 报告（如果传了 `--json-out`）。

## 4. 常见失败与排查

1. `start_pair` 失败
   - 端口被占用或端口名错误
   - 波特率/校验位/停止位配置不匹配
2. 单向转发失败
   - 虚拟串口配对关系写反
   - 实物接线方向错误（TX/RX 未交叉）
3. `missing proxy.data event`
   - 转发线程已报错（查看 UI 错误态和运行日志）
   - 端口有数据但未形成完整读写回路

## 5. 回归建议基线

- 开发回归：`--iterations 20 --soak-sec 0`
- 提交前回归：`--iterations 50 --soak-sec 300`
- 发版前回归：`--iterations 100 --soak-sec 1800`
