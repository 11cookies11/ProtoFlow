param(
  [string]$Python = "python",
  [string]$Node = "npm"
)

$ErrorActionPreference = "Stop"

$skillBundleSource = $env:PROTOFLOW_SKILL_BUNDLE_SOURCE
if ([string]::IsNullOrWhiteSpace($skillBundleSource)) {
  $skillBundleSource = Join-Path $PSScriptRoot "..\\..\\SkillForge\\dist\\skills"
}
$skillBundleSource = [System.IO.Path]::GetFullPath($skillBundleSource)
$skillStage = Join-Path $PSScriptRoot "..\\build\\packaging\\skills"

Write-Host "==> Prepare skill bundles"
if (Test-Path -LiteralPath $skillStage) { Remove-Item -LiteralPath $skillStage -Recurse -Force }
New-Item -ItemType Directory -Path $skillStage -Force | Out-Null
if (Test-Path -LiteralPath $skillBundleSource) {
  Copy-Item -Path (Join-Path $skillBundleSource "*") -Destination $skillStage -Recurse -Force
  Write-Host "Skill bundles staged from $skillBundleSource"
}
else {
  Write-Host "Skill bundle source not found, release package will not include real skills: $skillBundleSource"
}

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
  --add-data "build\\packaging\\skills;skills" `
  --add-data "config;config" `
  --add-data "plugins;plugins" `
  --add-data "ui\\assets;ui\\assets" `
  --add-data "VERSION;." `
  main.py
