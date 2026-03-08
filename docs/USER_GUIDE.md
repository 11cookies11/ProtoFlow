# ProtoFlow 用户手册（新版）

本文档面向一线用户，目标是让你在最短时间内：
- 能启动 ProtoFlow 并完成基础通信调试
- 能运行一份 DSL 自动化脚本
- 能根据模板编写自己的脚本
- 能定位常见错误

## 1. 软件定位
ProtoFlow 是一个通信自动化工具，不只是“串口收发器”。
它把通信流程拆成可执行步骤（DSL），用于：
- 串口 / TCP 调试
- 协议包调用（AT / SCPI / YMODEM / Modbus 等）
- 自动化测试与产测流程
- 过程日志与结果归档

## 2. 安装与启动

### 2.1 环境要求
- Python 3.11+
- Windows（当前仓库主要按 Windows 路径组织）
- 串口调试需要可用 COM 口

### 2.2 安装依赖
```bash
pip install -r requirements.txt
```

### 2.3 启动桌面版（推荐）
```bash
python main.py
```

说明：
- `main.py` 会启动 Qt + Web 前端的完整 UI。
- 运行日志默认写入 `%LOCALAPPDATA%/ProtoFlow/logs/`。

## 3. 5 分钟上手（第一次使用）

1. 启动软件后进入 `Manual` 页面。
2. 选择串口（Port）和波特率，点击连接。
3. 在发送框输入 `AT`（文本模式，勾选 `+CR/+LF` 视设备要求），点击发送。
4. 在右侧日志区确认收到 `OK` 或设备回包。
5. 切到 `Scripts` 页面，加载示例脚本并运行。

建议先用示例：
- `scripts/examples/at_command_flow_v01.yaml`
- `scripts/examples/scpi_flow_v01.yaml`

## 4. 界面功能说明

### 4.1 Manual（手动调试）
适合联机调试和定位通信问题。

主要能力：
- 串口连接 / 断开
- 文本与 HEX 两种发送模式
- 快捷指令管理（新增、编辑、删除、快速发送）
- IO 日志查看（ASCII/HEX 切换）
- 日志过滤、暂停、清空、导出

常用操作建议：
- 命令行设备优先用文本模式 + `CR/LF`。
- 二进制协议优先用 HEX 模式。
- 先用 Manual 确认链路通，再跑 Scripts 自动化。

### 4.2 Scripts（脚本运行）
适合批量执行流程（发送、等待、断言、解析、记录）。

主要能力：
- YAML 脚本加载/保存
- 运行、停止
- 运行日志查看
- 变量快照查看
- 执行进度显示

建议工作流：
1. 从 `scripts/examples/` 拷贝模板。
2. 先改 `params`（端口、地址、文件路径）。
3. 先跑通最小流程，再逐步加 `assert/parse/capture`。

### 4.3 Protocols（协议包）
用于查看当前可用的外置协议包（来自 `protocols/` 目录）。

当前行为：
- 可查看协议列表与元信息
- UI 内协议包为只读（不能在 UI 内新增/编辑/删除）

### 4.4 Proxy Monitor（透传监控，可选）
用于双串口透传与抓帧分析。

启用方式（二选一）：
- 环境变量：`PROTOFLOW_ENABLE_PROXY_MONITOR=1`
- 配置文件：`config/app.yaml` 中 `app.proxy_monitor_enabled: true`

未启用时，界面会隐藏/禁用相关能力。

### 4.5 Settings（设置）
可配置语言、主题、串口默认值、网络参数、工作目录等。

设置保存位置：
- `%LOCALAPPDATA%/ProtoFlow/config/ui_settings.json`

## 5. DSL 脚本入门

## 5.1 推荐版本
当前内置示例以 `version: "0.1"` 为主，建议新手优先使用 v0.1 示例模板快速上手。

## 5.2 最小可运行模板
```yaml
version: "0.1"

params:
  port: "COM3"
  baud: 115200

session:
  transport: serial
  port: "${port}"
  baud: "${baud}"
  data_bits: 8
  parity: none
  stop_bits: 1
  encoding: ascii
  eol: crlf

defaults:
  timeout_ms: 2000
  retry:
    count: 1
    backoff_ms: 200
    strategy: fixed

steps:
  - id: ping
    name: send
    text: "AT"

  - id: wait_ok
    name: expect
    match:
      type: contains
      pattern: "OK"

  - id: done_assert
    name: assert
    expr: "${last_rx_text} != ''"
    message: "no response"

artifacts:
  dir: "./runs/demo_${now}"
  raw_log: true
  summary_json: true
  report_csv: false
```

## 5.3 常用 Step（按使用频率）
- `send`: 发送文本/HEX
- `expect`: 等待并匹配响应（contains/regex/startswith）
- `sleep`: 延时
- `capture`: 正则提取到变量
- `assert`: 条件断言
- `if` / `loop`: 控制流
- `parse` / `path`: 结构化解析与字段提取
- `measure` / `assert_range`: 指标记录与范围校验
- `protocol.rpc` / `protocol.send` / `protocol.recv`: 调用外置协议包
- `switch_session`: 切换会话参数
- `exec` / `file`: 受控执行（受 security 白名单限制）

## 5.4 协议调用示例（AT）
```yaml
- id: at_ping
  name: protocol.rpc
  protocol: at_command
  request:
    cmd: "AT"
    eol: "crlf"
    expect:
      status: "ok"
  save_as: at_result

- id: assert_at
  name: assert
  expr: "${at_result.ok}"
  message: "AT command failed"
```

## 6. 产物与日志
脚本运行后可输出到 `artifacts.dir`：
- `raw_log.jsonl`: 过程明细
- `summary.json`: 结果汇总、错误码、变量快照
- `report.csv`: 可选报表

桌面运行日志：
- `%LOCALAPPDATA%/ProtoFlow/logs/web_ui_*.log`

## 7. 常见问题排查

### 7.1 连接失败
- 检查端口是否被其他工具占用
- 检查波特率/校验位/停止位是否与设备一致
- 先在 Manual 页面验证收发，再执行脚本

### 7.2 expect 超时
- 增大 `timeout_ms`
- 校验 `match.pattern` 是否正确
- 检查设备是否需要 `CR/LF`

### 7.3 变量为空导致断言失败
- 确认 `capture` 的正则组号和文本来源
- 先在日志中观察 `last_rx_text`

### 7.4 exec/file 被拒绝
- 在 `security` 中开启并配置白名单
- 错误码常见为 `EXEC_NOT_ALLOWED` 或 `FILE_NOT_ALLOWED`

### 7.5 代理监控不可见
- 检查是否启用 `proxy_monitor_enabled`
- 重启应用后再查看

## 8. 用户最佳实践
- 先手工、后自动：先在 Manual 确认设备链路，再迁移到 Scripts。
- 小步迭代：每次只加 1~2 个 step，随时运行验证。
- 先断言关键路径：对握手、关键响应、结果字段尽早 `assert`。
- 固化模板：把稳定流程沉淀到 `scripts/examples/` 或团队模板库。

## 9. 相关文档
- 项目概览：`README.md`
- 英文用户手册：`docs/USER_GUIDE_EN.md`
- v0.1 快速参考：`docs/YAML_DSL_V01_QUICKSTART.md`
- v0.2 规范与迁移：`docs/YAML_DSL_V02_SCHEMA_SPEC.md`、`docs/YAML_DSL_V02_MIGRATION_AND_BEST_PRACTICES.md`
- 协议包开发指南：`docs/PROTOCOL_PACKAGE_DEVELOPER_GUIDE.zh-CN.md`
