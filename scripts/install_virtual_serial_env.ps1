param(
  [string]$Pair1A = "COM11",
  [string]$Pair1B = "COM12",
  [string]$Pair2A = "COM13",
  [string]$Pair2B = "COM14",
  [switch]$InstallDriver = $true,
  [switch]$BootstrapChocolatey = $false
)

$ErrorActionPreference = "Stop"

function Write-Step([string]$text) {
  Write-Host "[STEP] $text" -ForegroundColor Cyan
}

function Test-Admin {
  $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
  $principal = New-Object Security.Principal.WindowsPrincipal($identity)
  return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Find-Setupc {
  $cmd = Get-Command setupc.exe -ErrorAction SilentlyContinue
  if ($cmd) {
    return $cmd.Source
  }

  $candidates = @(
    "C:\Program Files (x86)\com0com\setupc.exe",
    "C:\Program Files\com0com\setupc.exe"
  )
  foreach ($path in $candidates) {
    if (Test-Path $path) {
      return $path
    }
  }
  return $null
}

function Ensure-Com0ComInstalled {
  param(
    [switch]$TryInstall,
    [switch]$TryBootstrapChoco
  )

  $setupc = Find-Setupc
  if ($setupc) {
    return $setupc
  }

  if (-not $TryInstall) {
    return $null
  }

  $choco = Get-Command choco.exe -ErrorAction SilentlyContinue
  if ($choco) {
    Write-Step "Installing com0com via Chocolatey"
    & choco install com0com -y --no-progress | Out-Host
  } else {
    if ($TryBootstrapChoco) {
      Write-Step "Chocolatey not found. Bootstrapping Chocolatey"
      Set-ExecutionPolicy Bypass -Scope Process -Force
      [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
      Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
      $env:Path += ";$env:ALLUSERSPROFILE\chocolatey\bin"
      $choco = Get-Command choco.exe -ErrorAction SilentlyContinue
      if ($choco) {
        Write-Step "Installing com0com via Chocolatey"
        & choco install com0com -y --no-progress | Out-Host
      } else {
        Write-Warning "Chocolatey bootstrap failed. Install com0com manually, then rerun this script."
        return $null
      }
    } else {
      Write-Warning "Chocolatey not found. Re-run with -BootstrapChocolatey or install com0com manually."
      return $null
    }
  }

  $setupc = Find-Setupc
  return $setupc
}

function Get-SetupcList([string]$setupcPath) {
  try {
    return (& $setupcPath list 2>&1 | Out-String)
  } catch {
    return ""
  }
}

function Ensure-Pair {
  param(
    [string]$setupcPath,
    [string]$PortA,
    [string]$PortB
  )

  $listOutput = Get-SetupcList -setupcPath $setupcPath
  $hasA = $listOutput -match [regex]::Escape("PortName=$PortA")
  $hasB = $listOutput -match [regex]::Escape("PortName=$PortB")
  if ($hasA -and $hasB) {
    Write-Host "Pair exists: $PortA <-> $PortB" -ForegroundColor Green
    return
  }

  Write-Step "Creating pair: $PortA <-> $PortB"
  & $setupcPath install "PortName=$PortA" "PortName=$PortB"
}

function Show-SerialPorts {
  Write-Step "Enumerating serial ports"
  try {
    $ports = Get-CimInstance Win32_SerialPort | Select-Object -ExpandProperty DeviceID
    if ($ports) {
      $ports | Sort-Object | ForEach-Object { Write-Host $_ }
    } else {
      Write-Host "(no serial ports found)"
    }
  } catch {
    Write-Warning "Failed to enumerate serial ports by WMI: $($_.Exception.Message)"
  }
}

if (-not (Test-Admin)) {
  throw "Please run PowerShell as Administrator."
}

Write-Step "Checking com0com setup tool"
$setupcPath = Ensure-Com0ComInstalled -TryInstall:$InstallDriver -TryBootstrapChoco:$BootstrapChocolatey
if (-not $setupcPath) {
  throw "com0com is not installed. Install it manually and rerun."
}
Write-Host "setupc: $setupcPath" -ForegroundColor Green

Ensure-Pair -setupcPath $setupcPath -PortA $Pair1A -PortB $Pair1B
Ensure-Pair -setupcPath $setupcPath -PortA $Pair2A -PortB $Pair2B

Show-SerialPorts

Write-Host ""
Write-Host "Environment ready. Next commands:" -ForegroundColor Green
Write-Host ".\scripts\setup_proxy_test_env.ps1"
Write-Host ".\.venv\Scripts\python.exe scripts\proxy_regression.py --host-port $Pair1A --device-port $Pair2A --test-host-port $Pair1B --test-device-port $Pair2B --baud 115200 --iterations 30 --payload-size 64 --timeout-sec 2 --soak-sec 180 --json-out .\proxy_regression_report.json"
