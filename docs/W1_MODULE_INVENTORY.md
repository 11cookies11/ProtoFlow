# W1 模块清单（预填版）

## 使用说明

- 本文件已按当前仓库代码预填第一版。
- 本项目为个人项目，执行主体统一使用“你 + Codex”。
- 状态定义：`done`（已完整可用）、`partial`（可用但不完整）、`placeholder`（占位/演示为主）。

## 模块总览

| 模块 | 路径 | 职责 | 关键入口/类 | 主要依赖 | 状态 | 执行主体 |
|---|---|---|---|---|---|---|
| App Entry | `main.py`, `app/main_web.py` | 程序启动、日志初始化、组装运行时对象 | `main.py`, `app/main_web.py:165` | Qt, `EventBus`, `CommunicationManager`, `WebWindow` | partial | 你 + Codex |
| UI Frontend | `ui/frontend` | 页面交互、状态展示、桥接调用 | `ui/frontend/src/main.js:12`, `ui/frontend/src/App.vue` | Vue, Pinia, QWebChannel | partial | 你 + Codex |
| Desktop Host | `ui/desktop` | Qt WebEngine 宿主、WebChannel 桥接、窗口行为 | `ui/desktop/web_window.py`, `ui/desktop/web_bridge.py:27` | PySide6/PyQt6, WebChannel | partial | 你 + Codex |
| Comm Runtime | `infra/comm` | 串口/TCP 会话管理、统一收发事件 | `infra/comm/communication_manager.py:14`, `infra/comm/serial_manager.py:16`, `infra/comm/tcp_session.py:13` | pyserial, socket, `EventBus` | partial | 你 + Codex |
| Protocol Runtime | `infra/protocol` | 协议构帧/解帧、协议注册与加载 | `infra/protocol/protocol_loader.py`, `infra/protocol/registry.py` | 协议驱动实现、`EventBus` | partial | 你 + Codex |
| Packet Capture | `app/packet_engine.py` | RX/TX 事件分析、结构化帧输出 | `app/packet_engine.py:27` | `EventBus`, protocol utils | partial | 你 + Codex |
| DSL Runtime | `dsl_runtime` | YAML DSL 解析、状态机执行、动作注册 | `ui/desktop/script_runner_qt.py:100`, `dsl_runtime/lang/executor.py` | parser, actions, runtime context | partial | 你 + Codex |
| Plugin System | `app/plugin_manager.py`, `plugins` | 动态加载插件、扩展行为注入 | `app/plugin_manager.py:17` | importlib, `EventBus` | partial | 你 + Codex |
| Infra Common | `infra/common` | 事件总线与通用工具 | `infra/common/event_bus.py` | Python stdlib | done | 你 + Codex |
| Packaging/Build | `installer`, `scripts` | 安装包和构建脚本 | `installer/ProtoFlow.iss`, `scripts/build_windows.ps1` | Inno Setup, PowerShell | partial | 你 + Codex |
| Config/DSL Samples | `config` | 协议/DSL 示例与配置模板 | `config/*.yaml` | runtime loader | partial | 你 + Codex |
| Docs | `docs` | 用户文档、发布说明、计划文档 | `docs/USER_GUIDE.md`, `docs/PROJECT_PLAN.md` | Markdown | partial | 你 + Codex |

## 关键依赖链路（当前）

1. 启动链路  
`main.py` -> `app/main_web.py` -> `WebWindow` + `WebBridge` + `CommunicationManager` + `PluginManager` + `PacketAnalysisEngine`

2. UI 调用链路  
`ui/frontend/src/main.js` 建立 `QWebChannel` -> `window.bridge` -> `ui/desktop/web_bridge.py` 槽函数 -> `infra/comm` / `dsl_runtime`

3. 数据事件链路  
`SerialManager/TcpSession` 发布 `serial.* / tcp.*` -> `CommunicationManager` 转发为 `comm.*` -> UI 与抓包模块消费

4. 脚本执行链路  
`App.vue` 调用 `run_script` -> `ScriptRunnerQt` -> `dsl_runtime` parser/executor/actions -> 事件回传 UI

## 初步状态判断（W1）

1. 核心通信、桥接、脚本执行为“可运行但待稳定化”，统一标记 `partial`。
2. `Infra Common`（事件总线+工具）结构相对稳定，暂标 `done`。
3. 发布链路、文档链路存在但未形成标准化验收流程，标 `partial`。

## W1 待确认项

1. `Proxy/Capture` 是否存在“仅状态切换、未真实转发”的功能缺口，需集成验证。
2. 前端 fallback 页面触发条件与发布流程是否一致，避免误发布占位页。
3. 协议解析覆盖范围和准确率基线（尤其 Modbus RTU 之外）需要样本验证。
4. `partial` 模块的完成定义（DoD）需在 W2 冻结并写入验收标准。

## W1 输出物关联

- 占位审计：`docs/W1_PLACEHOLDER_AUDIT.md`
- 冒烟用例：`docs/W1_SMOKE_TEST_CASES.md`
- 总计划：`docs/PROJECT_PLAN.md`
