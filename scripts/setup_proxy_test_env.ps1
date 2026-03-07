param(
  [switch]$ShowPortsOnly
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
  Write-Error ".venv Python not found: $venvPython"
}

Write-Host "[1/4] Python:" -ForegroundColor Cyan
& $venvPython --version

Write-Host "[2/4] Validate pyserial:" -ForegroundColor Cyan
& $venvPython -c "import serial;print('pyserial ok:', serial.__version__)"

Write-Host "[3/4] Detect com0com driver:" -ForegroundColor Cyan
$driverFound = $false
foreach ($path in @(
  "HKLM:\SYSTEM\CurrentControlSet\Services\com0com",
  "HKLM:\SYSTEM\CurrentControlSet\Services\CNCA0"
)) {
  if (Test-Path $path) {
    $driverFound = $true
    Write-Host "Found registry key: $path"
  }
}
if (-not $driverFound) {
  Write-Warning "com0com driver not detected. Install com0com first (requires admin/UAC)."
}

Write-Host "[4/4] List serial ports:" -ForegroundColor Cyan
& $venvPython -c "import serial.tools.list_ports as p;ports=[x.device for x in p.comports()];print('\n'.join(ports) if ports else '(no serial ports found)')"

if ($ShowPortsOnly) {
  exit 0
}

Write-Host ""
Write-Host "Next step:" -ForegroundColor Green
Write-Host "After creating 2 virtual pairs (example COM11<->COM12 and COM13<->COM14), run:"
Write-Host ".\\.venv\\Scripts\\python.exe scripts\\proxy_regression.py --host-port COM11 --device-port COM13 --test-host-port COM12 --test-device-port COM14 --baud 115200 --iterations 30 --payload-size 64 --timeout-sec 2 --soak-sec 180 --json-out .\\proxy_regression_report.json"
