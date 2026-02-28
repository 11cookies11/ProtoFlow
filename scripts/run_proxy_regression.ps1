param(
  [ValidateSet("mock", "real")]
  [string]$Mode = "mock",
  [string]$HostPort = "COM11",
  [string]$DevicePort = "COM13",
  [string]$TestHostPort = "COM12",
  [string]$TestDevicePort = "COM14",
  [int]$Baud = 115200,
  [int]$Iterations = 30,
  [int]$PayloadSize = 64,
  [double]$TimeoutSec = 2.0,
  [int]$SoakSec = 180,
  [string]$JsonOut = ".\proxy_regression_report.json",
  [switch]$InjectDisconnect
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
  throw ".venv Python not found: $python"
}

if ($Mode -eq "mock") {
  Write-Host "[RUN] mock regression" -ForegroundColor Cyan
  $args = @(
    (Join-Path $PSScriptRoot "proxy_regression_mock.py"),
    "--iterations", $Iterations,
    "--payload-size", $PayloadSize,
    "--timeout-sec", $TimeoutSec,
    "--soak-sec", $SoakSec
  )
  if ($InjectDisconnect) {
    $args += "--inject-disconnect"
  }
  & $python @args
  exit $LASTEXITCODE
}

Write-Host "[RUN] real/virtual-port regression" -ForegroundColor Cyan
& $python (Join-Path $PSScriptRoot "proxy_regression.py") `
  --host-port $HostPort `
  --device-port $DevicePort `
  --test-host-port $TestHostPort `
  --test-device-port $TestDevicePort `
  --baud $Baud `
  --iterations $Iterations `
  --payload-size $PayloadSize `
  --timeout-sec $TimeoutSec `
  --soak-sec $SoakSec `
  --json-out $JsonOut

exit $LASTEXITCODE
