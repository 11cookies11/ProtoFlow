# 🚀 ToolOfCOM

🌐 Universal Communication & OTA Runtime Platform for Embedded Devices  
🧩 Protocol-Driven · Event-Flow Architecture · Pluggable Logic System

## 中文说明

### 🌟 什么是 ToolOfCOM？
ToolOfCOM 不是普通串口调试器，而是一个嵌入式通信运行时，具备：
- 🔌 多通信介质
- 📡 可配置协议 · ⚙️ FSM 驱动 OTA 升级
- 🧠 插件式逻辑扩展
- 🖥️ 图形化界面（Qt）

一句话：不写通信代码，只写配置与流程，由系统执行。

### 🧱 架构核心理念
```
              UI / MainWindow
    图形界面只负责展示，不参与逻辑或协议处理
                     ▲
                     │
                  EventBus
    系统总线：事件分发、行为触发、数据流转
                     ▲
        ┌───────────┴───────────┐
        │                       │
  ProtocolLoader         PluginManager
  协议解释器             逻辑扩展系统
        │                       │
        └───────┬───────┬───────┘
                │       │
           FSM Engine   │         CommunicationManager
    升级流程 YAML 驱动          串口 / TCP 统一入口
                │                       │
         SerialSession               TcpSession
    实体设备                       虚拟 MCU / Renode
```

### ✅ 这意味着什么？
| 概念 | 旧方式 | ToolOfCOM |
| --- | --- | --- |
| 协议 | 写死在代码 | YAML 配置 |
| 升级流程 | if/else | 有限状态机 FSM |
| 扩展性 | 难以扩展 | 插件无限扩展 |

### ⚡ 核心亮点
| 功能 | 描述 |
| --- | --- |
| 🔌 多通道通信 | 串口 UART / TCP / 可扩展 BLE、CAN |
| 📡 协议可配置 | header/length/CRC/command 写在 YAML |
| 🔁 事件架构 | 操作均为事件驱动 |
| ⚙️ FSM OTA | 升级逻辑由状态机执行 |
| 🧩 插件系统 | 写插件即扩展能力 |
| 🖥️ GUI | 可视化操作，无需命令行 |
| 🚀 OTA 体验 | 写 YAML，让系统跑流程 |

### 🧭 使用场景
- 💡 BootLoader 升级
- 🛠️ 嵌入式调试实验室
- 📦 生产线批量烧录
- 🌐 多设备运营 & 远程升级
- 🧪 Renode 虚拟 MCU 测试

### 🎯 为什么与众不同
它击穿了嵌入式调试的常见障碍：
| 障碍 | 传统方式 | ToolOfCOM |
| --- | --- | --- |
| 协议变动 | 改代码改配置 | 由 Session 抽象承载 |
| 逻辑扩展 | 重写流程 | 写插件 |

本质是 **Embedded Device Runtime System**，类似嵌入式通信界的 Node.js + Nginx + HomeAssistant 混合体。

### 📈 路线图
- v1.0 单设备通信与 OTA
- v2.0 多设备并行管理
- v3.0 分布式远程运营
- vX.X 嵌入式生态运行时

### 📝 一句总结
ToolOfCOM 是嵌入式设备的行为执行引擎——MCU 被编排，而非被手工操作。

---

## English Version

### 🌟 What is ToolOfCOM?
ToolOfCOM is not a plain serial console; it’s an embedded communication runtime with:
- 🔌 Multi-transport (Serial / TCP, extensible)
- 📡 Configurable protocol; FSM-driven OTA
- 🧩 Pluggable logic
- 🖥️ Qt GUI for visibility

In one line: describe flows in config, not in code—the system runs the logic.

### 🧱 Architecture
```
              UI / MainWindow
    UI presents data; no protocol/logic inside
                     ▲
                     │
                  EventBus
    Event backbone for dispatch and data flow
                     ▲
        ┌───────────┴───────────┐
        │                       │
  ProtocolLoader         PluginManager
  Protocol/framing       Logic extensions
        │                       │
        └───────┬───────┬───────┘
                │       │
           FSM Engine   │         CommunicationManager
   OTA flow driven by YAML        Unified entry for Serial / TCP
                │                       │
         SerialSession               TcpSession
    Physical device              Virtual MCU / Renode
```

### ✅ What it means
| Concept | Old way | ToolOfCOM |
| --- | --- | --- |
| Protocol | Hard-coded | YAML-configured |
| Upgrade flow | if/else | FSM |
| Extensibility | Rare | Plugins |

### ⚡ Highlights
| Feature | Description |
| --- | --- |
| 🔌 Multi-channel | UART / TCP / future BLE, CAN |
| 📡 Configurable protocol | header/length/CRC/command in YAML |
| 🔁 Event loop | Every step is event-driven |
| ⚙️ FSM OTA | State-machine-driven upgrade |
| 🧩 Plugin system | Add capabilities via plugins |
| 🖥️ GUI | Visual operations, no CLI required |
| 🚀 OTA | Write YAML, system drives the flow |

### 🧭 Use cases
- 💡 Bootloader upgrade
- 🛠️ Embedded lab testing
- 📦 Production-line flashing
- 🌐 Multi-device ops & remote upgrade
- 🧪 Renode virtual MCU testing

### 🎯 Why different
Breaks typical blockers:
| Obstacle | Traditional | ToolOfCOM |
| --- | --- | --- |
| Protocol changes | Modify code/config | Session abstraction |
| Logic extension | Rewrite flow | Add plugin |

Essentially an **Embedded Device Runtime System**—a blend of Node.js + Nginx + HomeAssistant for embedded comms.

### 📈 Roadmap
- v1.0 single-device comms & OTA
- v2.0 multi-device parallel mgmt
- v3.0 distributed remote ops
- vX.X embedded runtime ecosystem

### 📝 TL;DR
ToolOfCOM is a behavior execution engine for embedded devices—MCUs are orchestrated, not manually driven.
