# YAML-DSL v0.2 Schema 规范

日期：2026-03-06  
状态：Draft-Ready（v0.2）

## 1. 范围与验收
v0.2 目标：在 v0.1 可运行基础上，补齐“可用性”能力：
- 受控控制流：`if/else`、`loop`
- 结构化解析：`parse(json|kv|csv)` + `path`
- 产测能力：`measure`、`assert_range`
- 复用能力：`include/import`、`step_templates`、`profile`
- 受控执行：`exec`、`file`

验收口径：
- 覆盖调试/升级/参数写入/基础产测主流程。
- 所有失败都有标准错误对象（`code/message/step_id/ts`）。
- 产物能复盘每一步输入输出、耗时、断言与指标。

## 2. 顶层结构（v0.2）
```yaml
version: "0.2"
params: {}
vars: {}
profiles: {}          # 可复用会话配置
session: {}           # 直接会话；与 profile 二选一
defaults: {}
step_templates: {}    # 参数化步骤模板
steps: []
artifacts: {}
security: {}          # exec/file 的白名单约束
```

## 3. 新增/扩展 Step

### 3.1 `if`
```yaml
- name: if
  when: "${mode} == 'boot'"
  then: [ ...steps ]
  else: [ ...steps ]
```

### 3.2 `loop`
```yaml
- name: loop
  times: 5
  until: "${done} == true"   # 可选
  steps: [ ...steps ]
```

### 3.3 `parse`
```yaml
- name: parse
  format: json               # json | kv | csv
  source: "${last_rx_text}"
  save_as: "parsed"
```

### 3.4 `measure`
```yaml
- name: measure
  metric: "voltage"
  value: "${parsed.voltage}"
  unit: "V"
```

### 3.5 `assert_range`
```yaml
- name: assert_range
  value: "${parsed.voltage}"
  min: 11.8
  max: 12.2
  abs_err: 0.1      # 可选
  in_set: [12.0]    # 可选
```

### 3.6 `exec`（受控）
```yaml
- name: exec
  command: "tool.exe --check ${fw}"
  timeout_ms: 10000
  save_stdout_as: "exec_out"
```

### 3.7 `file`（受控）
```yaml
- name: file
  op: write_text            # read_text | write_text | append_text | exists
  path: "./runs/${now}/note.txt"
  content: "done=${result}"
```

## 4. 复用能力

### 4.1 `profiles`
```yaml
profiles:
  mcu_uart:
    transport: serial
    baud: 115200
    data_bits: 8
    parity: none
    stop_bits: 1
    encoding: ascii
    eol: crlf
```

### 4.2 `step_templates`
```yaml
step_templates:
  ping:
    params: [cmd]
    step:
      name: send
      text: "${cmd}"
```

### 4.3 `include/import`
```yaml
imports:
  - "./fragments/enter_boot.yaml"
```

## 5. Security 约束（v0.2）
```yaml
security:
  exec:
    enabled: true
    allow_commands: ["tool.exe", "python"]
    cwd_allowlist: ["./tools", "./runs"]
  file:
    root_allowlist: ["./runs", "./artifacts"]
```

## 6. 错误码（增量）
在 v0.1 基础上增加：
- `PARSE_FAILED`
- `RANGE_ASSERT_FAILED`
- `EXEC_NOT_ALLOWED`
- `EXEC_FAILED`
- `FILE_NOT_ALLOWED`
- `FILE_FAILED`

## 7. 迁移
- v0.1 脚本无需改动可继续执行。
- 使用 v0.2 新能力时需声明 `version: "0.2"`。
