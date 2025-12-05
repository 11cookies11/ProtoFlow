# ToolOfCOM

一个基于事件驱动的通信与 OTA 工具，支持串口/TCP 通道、协议帧解析、插件扩展和 Qt 界面。

## 主要特性
- **事件总线**：`core/event_bus.py` 解耦模块，所有通信与业务事件通过 bus 流转。
- **多通道通信**：`SerialManager`（串口）、`TcpSession`（TCP），由 `CommunicationManager` 统一入口，转发为 `comm.*` 事件。
- **协议装载/帧解析**：`ProtocolLoader` 根据 `config/protocol.yaml` 构造/解析帧，支持 CRC16/CRC8。
- **OTA 状态机**：`FsmEngine` 从 `config/ota_fsm.yaml` 读取状态机，事件驱动的 OTA 流程。
- **插件机制**：`PluginManager` 动态加载 `plugins/*.py`，支持 `register(bus)` 或 `register(bus, protocol)`。
- **示例插件**：`plugins/ota_upgrade.py`（OTA 发送流程）、`example_plugin.py`（帧打印）。
- **Qt 界面**：`ui/main_window.py` 基于 PySide6/PyQt6，支持通信方式选择（串口/TCP）、发送/日志展示。

## 目录结构
```
ToolOfCOM/
 ├── core/                # 核心模块
 │    ├── event_bus.py
 │    ├── communication_manager.py
 │    ├── serial_manager.py
 │    ├── tcp_session.py
 │    ├── protocol_loader.py
 │    ├── fsm_engine.py
 │    └── plugin_manager.py
 ├── ui/
 │    └── main_window.py   # Qt 主界面
 ├── config/
 │    ├── protocol.yaml    # 帧格式、命令定义
 │    ├── ota_fsm.yaml     # OTA 状态机配置
 │    └── app.yaml         # 预留
 ├── plugins/
 │    ├── example_plugin.py
 │    └── ota_upgrade.py
 ├── assets/icons/         # 资源占位
 ├── src/com_tool.py       # COM 调试脚本
 └── main.py               # 应用入口
```

## 快速开始
1) 创建并激活虚拟环境（PowerShell）：
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
2) 安装依赖（如需代理可设置 HTTP_PROXY/HTTPS_PROXY 或直连环境变量）：
```powershell
$env:NO_PROXY='*'; $env:PIP_NO_PROXY='*'; $env:HTTP_PROXY=''; $env:HTTPS_PROXY='';
python -m pip install -r requirements.txt
```
3) 运行 GUI：
```powershell
python .\main.py
```
4) 调试协议帧（可选，COM 调试脚本）：
```powershell
python .\src\com_tool.py --prog-id "Your.ProgID" --method "Ping" --args "hello"
```

## 事件流与模块协作
- `CommunicationManager` 负责串口/TCP 选择与发送，输出 `comm.rx/tx/connected/disconnected/error`。
- `ProtocolLoader` 订阅 `serial.rx`，发布 `protocol.frame`；`send` 时发布 `protocol.tx`（由 CommunicationManager 发送）。
- `FsmEngine` 订阅 `ota.start` 与 `protocol.frame`，按 `ota_fsm.yaml` 迁移，结束时发布 `ota.done`。
- 插件可订阅 bus 事件扩展功能，示例见 `plugins/ota_upgrade.py`。

## 配置说明
- `config/protocol.yaml`：定义 header/tail/crc/max_length、commands。
- `config/ota_fsm.yaml`：定义状态机（send/wait/next/loop/exit）；可根据设备协议调整。

## 插件开发
在 `plugins/your_plugin.py` 中实现：
```python
PLUGIN_NAME = "your_plugin"
def register(bus, protocol=None):
    bus.subscribe("protocol.frame", handler)
```
加载成功后会发布 `plugin.loaded`，异常发布 `plugin.error`。

## OTA 示例流程
- UI 触发 `ota.start` 或插件自定义事件。
- `FsmEngine` 按配置驱动 `ProtocolLoader.send`，设备回包触发 `protocol.frame` 进一步迁移。
- `plugins/ota_upgrade.py` 提供写块示例，发布 `ota.status/finished/error` 供 UI 展示。

## 常见问题
- **Qt 未安装**：执行 `python -m pip install "PySide6>=6.6"`（或换 PyQt6）。
- **代理报错 `check_hostname requires server_hostname`**：清空空代理或设置正确的 HTTP_PROXY/HTTPS_PROXY。
- **串口权限/位数**：Python 与目标 COM/驱动需位数匹配，必要时以管理员运行。
