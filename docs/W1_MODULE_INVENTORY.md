# W1 模块清单（模板）

## 使用说明

- 填写当前仓库模块、职责、入口、依赖关系和状态。
- 状态建议使用：`done`、`partial`、`placeholder`。

## 模块总览

| 模块 | 路径 | 职责 | 关键入口 | 主要依赖 | 状态 | 负责人 |
|---|---|---|---|---|---|---|
| UI Frontend | `ui/frontend` | 前端页面与交互 | `src/main.js` | Vue, Pinia, QWebChannel | partial | 待定 |
| Desktop Host | `ui/desktop` | Qt 宿主与桥接 | `web_window.py` | PySide6/PyQt6 | partial | 待定 |
| App Core | `app` | 启动、插件、抓包引擎 | `main_web.py` | infra, dsl_runtime | partial | 待定 |
| Comm | `infra/comm` | 串口/TCP 通信 | `communication_manager.py` | pyserial, socket | partial | 待定 |
| Protocol | `infra/protocol` | 协议封装与加载 | `protocol_loader.py` | registry | partial | 待定 |
| DSL Runtime | `dsl_runtime` | DSL 解析与执行 | `lang/executor.py` | actions, engine | partial | 待定 |
| Plugins | `plugins` | 插件扩展机制 | `example_plugin.py` | app.plugin_manager | partial | 待定 |

## 依赖关系备注

- 记录跨模块依赖、循环依赖风险、解耦建议。

## 待确认项

1.  
2.  
3.  

