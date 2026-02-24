# W7-02 Windows 打包产物校验

## 目标

- 确保打包后目录结构与运行时代码预期一致。
- 在发布前尽早发现“资源路径错位”导致的启动失败问题。

## 构建脚本调整

- `scripts/build_windows.ps1` 已更新：
  - `ui/frontend/dist` -> `frontend/dist`
  - `ui/assets` -> `assets`
  - 构建后自动执行 `scripts/validate_windows_bundle.ps1`

## 校验脚本

- `scripts/validate_windows_bundle.ps1`

执行：

```powershell
powershell -File scripts/validate_windows_bundle.ps1 -BundleRoot dist\ProtoFlow
```

## 必检路径

- `ProtoFlow.exe`
- `frontend/dist/index.html`
- `assets/web/index.html`
- `assets/icons/logo.svg` 或 `assets/icons/logo.png`
- `config/`
