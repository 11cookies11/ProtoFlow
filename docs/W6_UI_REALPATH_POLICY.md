# W6-01 UI 真实路径策略（去除默认 fallback 依赖）

## 变更

- `ui/desktop/web_window.py` 默认只加载：
  - `frontend/dist/index.html`
- 当 dist 缺失时，应用直接报错退出，不再自动回退占位页。

## 例外（仅本地临时调试）

- 允许通过环境变量显式开启 fallback：
  - `PROTOFLOW_ALLOW_WEB_FALLBACK=1`
- 启用后仅在 `assets/web/index.html` 存在时回退。

## 目的

- 核心页面运行路径默认指向真实前端产物，减少 mock/fallback 误用风险。
- 与发布门禁策略一致（dist 缺失视为完整性失败）。
