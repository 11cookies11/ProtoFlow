param(
  [string]$BundleRoot = "dist\ProtoFlow"
)

$ErrorActionPreference = "Stop"

function Assert-PathExists {
  param(
    [string]$Path,
    [string]$Hint
  )
  if (-not (Test-Path -LiteralPath $Path)) {
    throw "Missing required bundle path: $Path`nHint: $Hint"
  }
}

Write-Host "==> Bundle root: $BundleRoot"
Assert-PathExists -Path $BundleRoot -Hint "Run build_windows.ps1 first."

$exe = Join-Path $BundleRoot "ProtoFlow.exe"
Assert-PathExists -Path $exe -Hint "PyInstaller output should contain ProtoFlow.exe."

$frontendIndex = Join-Path $BundleRoot "frontend\dist\index.html"
Assert-PathExists -Path $frontendIndex -Hint "Web runtime expects frontend/dist/index.html."

$assetsWeb = Join-Path $BundleRoot "assets\web\index.html"
Assert-PathExists -Path $assetsWeb -Hint "Local fallback page should exist in assets/web."

$assetsLogoSvg = Join-Path $BundleRoot "assets\icons\logo.svg"
$assetsLogoPng = Join-Path $BundleRoot "assets\icons\logo.png"
if (-not (Test-Path -LiteralPath $assetsLogoSvg) -and -not (Test-Path -LiteralPath $assetsLogoPng)) {
  throw "Missing app icon in bundle: expected assets\icons\logo.svg or logo.png"
}

$configDir = Join-Path $BundleRoot "config"
Assert-PathExists -Path $configDir -Hint "Runtime config directory should be packed."

Write-Host "[OK] Windows bundle layout is valid."
