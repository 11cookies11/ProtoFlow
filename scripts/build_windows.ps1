param(
  [string]$Python = "python",
  [string]$Node = "npm"
)

$ErrorActionPreference = "Stop"

Write-Host "==> Build web UI"
Push-Location "web-ui"
& $Node ci
& $Node run build
Pop-Location

Write-Host "==> Install Python deps"
& $Python -m pip install --upgrade pip
& $Python -m pip install -r requirements.txt

Write-Host "==> Build app (PyInstaller)"
& $Python -m PyInstaller --name ProtoFlow --windowed --onedir --noconfirm --icon "installer\ProtoFlow.ico" `
  --add-data "web-ui\dist;web-ui\dist" `
  --add-data "config;config" `
  --add-data "plugins;plugins" `
  --add-data "assets;assets" `
  main.py

Write-Host "==> Generate installer icon"
if (-not (Test-Path -LiteralPath "installer\\ProtoFlow.ico")) {
  & powershell -File scripts\generate_icon.ps1 -Source assets\\icons\\logo.png -Output installer\\ProtoFlow.ico -Size 256
}
