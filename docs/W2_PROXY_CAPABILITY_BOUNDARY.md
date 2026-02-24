# W2-UF003 Proxy 能力边界与 UI 文案对齐说明

## 目标
- 明确当前版本 Proxy 的真实能力边界。
- 保证 UI 文案与真实行为一致，避免“显示运行中=已建立实时转发”的误导。

## 当前能力结论（W2）
- 当前默认能力：`config-only`
- 支持内容：
  - 代理对配置的增删改查（名称、端口、串口参数、状态落盘）
  - 抓包开关控制（`start_capture` / `stop_capture`）
  - 状态展示与配置管理流程
- 不支持内容（本期）：
  - 实时串口透传引擎（端口 A -> 端口 B 的真实字节转发）

## 前后端对齐证据
- 后端默认 capability：
  - `ui/desktop/web_bridge.py` 中 `create_proxy_pair` 默认 `capability: "config-only"`
- 前端状态展示逻辑：
  - `ui/frontend/src/components/ProxyMonitorView.vue` 中 `deriveProxyPresentation(...)`
  - 当 `status=running` 且 `capability=config-only`：
    - 状态文案：`配置已启用`
    - 路由文案：`未建立实时转发`
- 页面说明文案：
  - `ProxyMonitorView.vue` 提示：
    - 当前版本以代理配置管理和抓包分析为主
    - “配置已启用”不代表已建立实时串口转发链路

## 验收口径（UF003 Done）
- 打开 Proxy 监控页可见能力说明文案。
- 将任意代理切换到“启用”后：
  - 显示 `配置已启用`
  - 同时显示 `未建立实时转发`
- 后端返回默认 capability 仍为 `config-only`。

## 后续演进（非 W2 范围）
- 若实现真实透传引擎，需新增能力值 `realtime-forward` 并同步：
  - 后端真实转发生命周期
  - UI 状态映射（可显示“运行中/转发中”）
  - 回归用例与风险控制
