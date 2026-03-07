# YAML-DSL v0.1 Schema 规范

日期：2026-03-06  
状态：Draft-Ready（用于实现）

## 1. 目标与边界
- 直接替代旧 DSL 语法，不做兼容层。
- v0.1 仅覆盖 MVP：`session + send/expect/sleep + capture + retry/on_fail + assert + artifacts`。
- 面向单设备单会话（serial 优先）。

## 2. 顶层结构
```yaml
version: "0.1"
params: {}         # 运行前注入
vars: {}           # 运行时初始变量
session: {}        # 串口会话配置
defaults: {}       # 默认超时/重试策略
steps: []          # 顺序步骤
artifacts: {}      # 日志与产物导出配置
```

必填：
- `version`
- `session`
- `steps`

## 3. Session
```yaml
session:
  transport: serial
  port: "${port}"
  baud: 115200
  data_bits: 8
  parity: none
  stop_bits: 1
  encoding: ascii      # ascii | utf8 | hex
  eol: crlf            # none | cr | lf | crlf
  open_timeout_ms: 3000
  read_timeout_ms: 200
```

约束：
- `transport` v0.1 固定为 `serial`。
- 运行期允许 `switch_session`（端口/波特率切换）作为扩展 step。

## 4. Defaults
```yaml
defaults:
  timeout_ms: 2000
  retry:
    count: 0
    backoff_ms: 0
    strategy: fixed     # fixed | exponential
  drain_before_expect: false
  consume_on_match: true
```

## 5. Step 通用字段
每个 step 为一个对象，通用字段：
- `id`：唯一标识（建议）
- `name`：类型（`send|expect|sleep|assert|capture|if|loop`）
- `timeout_ms`：覆盖默认超时
- `retry`：覆盖默认重试
- `on_fail`：失败时执行的步骤列表（局部补救）

示例：
```yaml
- id: enter_boot
  name: send
  text: "+++BOOT"
  eol: cr
  retry: { count: 2, backoff_ms: 150, strategy: exponential }
  on_fail:
    - name: send
      text: "AT+RST"
```

## 6. Step 类型定义

### 6.1 `send`
```yaml
- name: send
  text: "AT+GMR"         # text 与 hex 二选一
  hex: "41 54 0D 0A"
  eol: lf                # 可选，覆盖 session.eol
  encoding: ascii        # 可选，覆盖 session.encoding
```

### 6.2 `expect`
```yaml
- name: expect
  match:
    type: regex          # contains | regex | startswith
    pattern: "OK|READY"
    flags: "i"           # 可选：i,m,s
  capture:
    - var: version
      regex: "VER:([0-9.]+)"
      group: 1
  save_as: last_line     # 可选，保存命中行
```

### 6.3 `sleep`
```yaml
- name: sleep
  ms: 500
```

### 6.4 `capture`（独立抓取）
```yaml
- name: capture
  source: "${last_line}"     # 默认最近接收行
  regex: "SN:([A-Z0-9]+)"
  group: 1
  var: device_sn
```

### 6.5 `assert`
```yaml
- name: assert
  any:
    - match: { type: contains, pattern: "PASS" }
    - expr: "${voltage} >= 11.8 and ${voltage} <= 12.2"
  message: "self test failed"
```

说明：
- `any` / `all` 二选一；`expr` 使用受限表达式引擎。

### 6.6 `if`（v0.1 受控）
```yaml
- name: if
  when: "${need_boot} == true"
  then:
    - name: send
      text: "boot"
  else:
    - name: send
      text: "app"
```

### 6.7 `loop`（v0.1 受控）
```yaml
- name: loop
  times: 3
  steps:
    - name: send
      text: "AT"
    - name: expect
      match: { type: contains, pattern: "OK" }
```

## 7. 可靠性语义

### 7.1 重试
- `retry.count`：失败后最多重试次数。
- `backoff_ms`：重试间隔。
- `strategy=exponential`：第 n 次等待 `backoff_ms * 2^(n-1)`。

### 7.2 失败判定
step 失败条件：
- 超时（`READ_TIMEOUT` / `STEP_TIMEOUT`）
- 匹配失败（`MATCH_FAILED`）
- 抓取失败（`CAPTURE_FAILED`）
- 断言失败（`ASSERT_FAILED`）
- 发送失败（`WRITE_FAILED`）

### 7.3 on_fail
- 在本 step 最终失败后执行 `on_fail`。
- `on_fail` 执行失败不吞掉原始错误，最终错误仍为原 step 错误码。

## 8. 模板与变量

### 8.1 模板风格
v0.1 固定使用：`${var}`。

### 8.2 变量来源
- `params`：外部输入（运行前）
- `vars`：脚本初值
- `capture/assert/expect`：运行中写入

### 8.3 变量优先级
运行时读取优先级：`vars(runtime) > params > vars(initial)`。

## 9. Artifacts
```yaml
artifacts:
  dir: "./runs/${now}"
  raw_log: true
  summary_json: true
  report_csv: false
```

最低要求：
- `raw_log`：逐条收发与 step 日志
- `summary.json`：结果、耗时、失败点、最终变量快照

## 10. 错误模型
统一错误对象：
```yaml
error:
  code: "MATCH_FAILED"
  message: "expect regex not matched"
  step_id: "wait_ok"
  ts: 1741220000.123
```

标准错误码（v0.1）：
- `OPEN_FAILED`
- `PORT_BUSY`
- `SWITCH_FAILED`
- `WRITE_FAILED`
- `READ_TIMEOUT`
- `MATCH_FAILED`
- `CAPTURE_FAILED`
- `ASSERT_FAILED`
- `STEP_TIMEOUT`
- `UNEXPECTED_EXCEPTION`

## 11. 最小完整示例
```yaml
version: "0.1"

params:
  port: "COM5"
  fw_ver_expected: "1.2.3"

vars:
  version: ""

session:
  transport: serial
  port: "${port}"
  baud: 115200
  data_bits: 8
  parity: none
  stop_bits: 1
  encoding: ascii
  eol: crlf
  open_timeout_ms: 3000
  read_timeout_ms: 200

defaults:
  timeout_ms: 2000
  retry: { count: 1, backoff_ms: 200, strategy: fixed }

steps:
  - id: ping
    name: send
    text: "AT"

  - id: wait_ok
    name: expect
    match: { type: contains, pattern: "OK" }

  - id: read_ver
    name: send
    text: "AT+GMR"

  - id: parse_ver
    name: expect
    match: { type: regex, pattern: "VER:([0-9.]+)" }
    capture:
      - var: version
        regex: "VER:([0-9.]+)"
        group: 1

  - id: assert_ver
    name: assert
    all:
      - expr: "${version} == ${fw_ver_expected}"
    message: "version mismatch"

artifacts:
  dir: "./runs/${now}"
  raw_log: true
  summary_json: true
  report_csv: false
```

## 12. 实现顺序建议
1. parser 校验顶层 schema 与 step 基础字段  
2. session manager 与串口独占  
3. `send/expect/sleep`  
4. `capture/assert/retry/on_fail`  
5. artifacts 与 summary 输出  
