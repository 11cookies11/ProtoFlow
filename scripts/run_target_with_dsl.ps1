param(
  [Parameter(Mandatory=$true)][string]$HostPort,
  [Parameter(Mandatory=$true)][string]$TargetPort,
  [string]$Scenario = ".\tools\target_emulator\scenarios\at_basic.yaml",
  [string]$DslScript = ".\scripts\examples\target_at_smoke_v02.yaml",
  [int]$Baud = 115200
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"
if (!(Test-Path $python)) {
  $python = "python"
}

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$emuOut = Join-Path $root "runs\target_emu_$ts"

Write-Host "[1/3] Start target emulator on $TargetPort ..." -ForegroundColor Cyan
$emuArgs = @(
  "$root\scripts\target_emulator.py",
  "--scenario", (Resolve-Path $Scenario),
  "--mode", "serial",
  "--serial-port", $TargetPort,
  "--baud", "$Baud",
  "--artifacts-dir", $emuOut
)
$emu = Start-Process -FilePath $python -ArgumentList $emuArgs -PassThru -WindowStyle Hidden
Start-Sleep -Milliseconds 500

try {
  Write-Host "[2/3] Run DSL against host port $HostPort ..." -ForegroundColor Cyan
  $env:PROTOFLOW_PROTOCOLS_DIR = Join-Path $root "protocols"
  & $python "$root\app\dsl_main.py" (Resolve-Path $DslScript)
  $code = $LASTEXITCODE
  if ($code -ne 0) {
    throw "DSL run failed with code $code"
  }
}
finally {
  Write-Host "[3/3] Stop target emulator ..." -ForegroundColor Cyan
  if ($emu -and !$emu.HasExited) {
    Stop-Process -Id $emu.Id -Force
  }
}

Write-Host "Done. Emulator artifacts: $emuOut" -ForegroundColor Green
