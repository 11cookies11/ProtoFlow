$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$hostPort = $env:TARGET_HOST_PORT
$devicePort = $env:TARGET_DEVICE_PORT

if ([string]::IsNullOrWhiteSpace($hostPort) -or [string]::IsNullOrWhiteSpace($devicePort)) {
  Write-Host "[SKIP] TARGET_HOST_PORT / TARGET_DEVICE_PORT not configured; skip virtual-serial nightly regression."
  exit 0
}

$python = "python"
$scenario = Join-Path $root "tools\target_emulator\scenarios\at_basic.yaml"
$dsl = Join-Path $root "scripts\examples\target_at_smoke_v02.yaml"
$out = Join-Path $root ("runs\nightly_target_emu_" + (Get-Date -Format "yyyyMMdd_HHmmss"))

Write-Host "[1/3] Start target emulator on $devicePort ..."
$emuArgs = @(
  "$root\scripts\target_emulator.py",
  "--scenario", $scenario,
  "--mode", "serial",
  "--serial-port", $devicePort,
  "--baud", "115200",
  "--artifacts-dir", $out
)
$emu = Start-Process -FilePath $python -ArgumentList $emuArgs -PassThru -WindowStyle Hidden
Start-Sleep -Milliseconds 500

try {
  Write-Host "[2/3] Run DSL smoke on $hostPort ..."
  $env:PROTOFLOW_PROTOCOLS_DIR = Join-Path $root "protocols"
  & $python "$root\app\dsl_main.py" $dsl
  if ($LASTEXITCODE -ne 0) {
    throw "dsl_main failed with code $LASTEXITCODE"
  }
}
finally {
  Write-Host "[3/3] Stop target emulator ..."
  if ($emu -and !$emu.HasExited) {
    Stop-Process -Id $emu.Id -Force
  }
}

Write-Host "Nightly virtual-serial regression passed. artifacts=$out"
