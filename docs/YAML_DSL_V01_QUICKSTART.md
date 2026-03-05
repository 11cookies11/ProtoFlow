# YAML-DSL v0.1 快速开始

日期：2026-03-06

## 1. 当前实现范围
v0.1 当前已实现：
- `session`（serial 参数解析）
- `send`
- `expect`（contains/regex/startswith + timeout_ms）
- `sleep`
- `capture`（regex 提取变量）
- `assert`（match/expr，支持 all/any）
- `retry/backoff/on_fail`
- `raw_log + summary.json` 产物导出

## 2. 最小示例
```yaml
version: "0.1"

params:
  port: "COM5"

vars:
  ver: ""

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
  - name: send
    text: "AT+GMR"
  - name: expect
    match: { type: regex, pattern: "VER:([0-9.]+)" }
    capture:
      var: ver
      regex: "VER:([0-9.]+)"
      group: 1
  - name: assert
    expr: "${ver} != ''"
    message: "version parse failed"

artifacts:
  dir: "./runs/v01_${now}"
  raw_log: true
  summary_json: true
  report_csv: false
```

## 3. 运行入口
CLI:
```bash
python app/dsl_main.py path/to/script.yaml
```

桌面端：
- 打开 Scripts 页面，加载/粘贴 v0.1 YAML 后运行。

## 4. 产物输出
默认输出目录由 `artifacts.dir` 指定，支持 `${now}` 模板。

输出文件：
- `raw_log.jsonl`: 每步执行记录
- `summary.json`: 执行摘要、错误信息、变量快照
- `report.csv`: 可选导出

## 5. 回归脚本
```bash
python scripts/v01_dsl_regression.py
```

覆盖项：
- 执行成功路径（send/expect/capture/assert）
- 失败恢复（retry + on_fail）
- 产物导出（raw_log/summary）

## 6. 约束与注意事项
- 当前 `session.transport` 仅支持 `serial`。
- v0.1 尚未完成的 step 将显式抛出 `NotImplementedError`。
- 表达式优先使用 `${var}` 变量引用形式。
