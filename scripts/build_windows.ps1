param(
  [string]$Python = "python",
  [string]$Node = "npm"
)

$ErrorActionPreference = "Stop"

Write-Host "==> Build web UI"
Push-Location "ui\\frontend"
& $Node ci
& $Node run build
Pop-Location

Write-Host "==> Install Python deps"
& $Python -m pip install --upgrade pip
& $Python -m pip install -r requirements.txt

Write-Host "==> Regenerate installer/app icon from current logo"
& powershell -File scripts\generate_icon.ps1 -Source ui\\assets\\icons\\logo.png -Output installer\\ProtoFlow.ico -Size 256

Write-Host "==> Build app (PyInstaller)"
if (Test-Path -LiteralPath "build\\ProtoFlow") { Remove-Item -LiteralPath "build\\ProtoFlow" -Recurse -Force }
if (Test-Path -LiteralPath "dist\\ProtoFlow") { Remove-Item -LiteralPath "dist\\ProtoFlow" -Recurse -Force }
& $Python -m PyInstaller --name ProtoFlow --windowed --onedir --noconfirm --clean --icon "installer\ProtoFlow.ico" `
  --add-data "ui\\frontend\\dist;ui\\frontend\\dist" `
  --add-data "config;config" `
  --add-data "plugins;plugins" `
  --add-data "ui\\assets;ui\\assets" `
  --add-data "VERSION;." `
  main.py
