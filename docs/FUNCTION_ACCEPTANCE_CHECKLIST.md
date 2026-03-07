# 功能验收清单（P0）

> 目标：用于“发售前功能闭环”逐项打勾。  
> 约束：当前阶段不包含 TCP 开发项。

## 1. 代理监控

- [x] 代理对增删改查可用
- [x] 端口选择来自真实串口枚举（无端口时有回退）
- [x] 端口参数校验有效（端口非空、两端口不可相同）
- [x] 代理开关真实驱动后端会话（非 UI 假状态）
- [x] 删除代理会先停止会话，避免资源残留
- [x] 状态可见：`running / stopped / error`
- [x] 异常可见：卡片显示错误信息
- [x] 异常恢复：卡片支持“一键重试”

## 2. 抓包联动

- [x] 转发数据发布 `proxy.data`
- [x] 抓包引擎可消费 `proxy.data` 并产出 `capture.frame`
- [x] 抓包方向语义稳定（基于 host/device 角色）
- [x] 通道语义稳定（未指定目标时归一到 host_port）
- [x] 抓包停止后不再追加帧
- [x] 协议异常帧可识别（短帧/CRC 错误/长度异常）
- [x] 异常帧在抓包列表高亮提示

## 3. 状态持久化与恢复

- [x] 代理配置持久化
- [x] `desiredActive` 持久化用户期望状态
- [x] 冷启动按 `desiredActive` 尝试恢复会话
- [x] 恢复结果回写 `running/stopped/error`
- [x] 应用退出统一 `stop_all`，避免残留会话

## 3.1 DSL 运行状态

- [x] 启动后可进入运行态并推进状态机
- [x] 停止操作可回传停止态
- [x] 运行异常可回传错误态
- [x] 中文环境脚本加载不因编码失败

## 4. 构建与运行一致性

- [x] 前端构建通过（`npm run build`）
- [x] 后端关键模块语法检查通过（`py_compile`）
- [x] 打包版本信息读取链路可用（`VERSION` 资源）

## 5. 回归测试能力

- [x] 有真实/虚拟串口回归脚本：`scripts/proxy_regression.py`
- [x] 有无驱动 mock 回归脚本：`scripts/proxy_regression_mock.py`
- [x] 有环境检查脚本：`scripts/setup_proxy_test_env.ps1`
- [x] 有一键入口：`scripts/run_proxy_regression.ps1`
- [ ] 真实设备执行（双串口回环）
- [ ] 真实设备执行（异常拔插）
- [ ] 真实设备执行（长稳 soak）

## 5.1 配置持久化损坏回退

- [x] 配置文件写入采用原子替换，避免半写入文件
- [x] 主配置 JSON 损坏时可自动回退到 `.bak`
- [x] 回退后主配置文件会自动修复为可解析 JSON
- [x] 回归脚本 `scripts/config_persistence_regression.py` 通过

## 5.2 打包运行一致性

- [x] PyInstaller spec 包含 `ui/frontend/dist`、`config`、`plugins`、`ui/assets`、`VERSION`
- [x] `scripts/build_windows.ps1` 包含与 spec 一致的数据打包项
- [x] `installer/ProtoFlow.iss` 使用 `MyAppVersion` 宏生成安装包版本号
- [x] 运行日志默认写入 `%LOCALAPPDATA%/ProtoFlow/logs`
- [x] 回归脚本 `scripts/package_runtime_regression.py` 通过

## 6. 验收结论模板

- 版本：`<填写 VERSION>`
- 验收日期：`<YYYY-MM-DD>`
- 执行人：`<姓名>`
- 结论：
  - [ ] 通过
  - [ ] 有阻塞项（列出）
