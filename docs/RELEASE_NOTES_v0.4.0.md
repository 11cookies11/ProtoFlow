# ProtoFlow v0.4.0（发布说明草案）

对比基线：`v0.3.2..HEAD`

## 版本重点
- 核心链路回归自动化补齐：新增一键门禁脚本 `scripts/core_regression_gate.py`，覆盖串口连接、收发、脚本生命周期与协议回放关键路径。
- Windows 打包校验接入构建流程：`scripts/build_windows.ps1` 构建后自动执行 `scripts/validate_windows_bundle.ps1`，在缺少关键产物时快速失败。
- 前端真实链路策略收敛：默认不再自动回退到 web 开发页；仅在显式设置 `PROTOFLOW_ALLOW_WEB_FALLBACK=1` 时启用临时回退。

## 功能与行为变更
- Proxy 状态新增 `configured`，用于表示“已配置但未运行转发”的实例，避免与 `running` 语义混淆。
- Capture 状态由后端统一下发并通过 `capture_status` 信号透传到前端，UI 状态与后端真实运行态保持一致。
- 串口高级参数生效链路回归覆盖增强，连接状态与 UI 展示偏差问题已修复。

## 运维与发布
- 推荐发布前执行：
  - `python scripts/core_regression_gate.py --serial-mode mock --serial-cycles 50`
  - `powershell -File scripts/validate_windows_bundle.ps1 -BundleRoot dist\\ProtoFlow`
- 如需本地临时页面回退（仅开发场景）：
  - PowerShell: `$env:PROTOFLOW_ALLOW_WEB_FALLBACK='1'`
  - 生产发布包不建议启用。

## 文档同步
- 更新 `docs/USER_GUIDE.md`：补充运行策略、Proxy/Capture 状态说明与发布前检查建议。
- 更新 `docs/W7_RELEASE_DOC_CHECKLIST.md`：形成可执行发布核对项。
