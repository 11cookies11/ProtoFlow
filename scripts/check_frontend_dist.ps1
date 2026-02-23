param(
  [string]$DistDir = "ui\\frontend\\dist"
)

$ErrorActionPreference = "Stop"

$indexPath = Join-Path $DistDir "index.html"

if (-not (Test-Path -LiteralPath $DistDir)) {
  throw "Frontend dist directory not found: $DistDir"
}

if (-not (Test-Path -LiteralPath $indexPath)) {
  throw "Frontend dist entry not found: $indexPath"
}

Write-Host "Frontend dist check passed: $indexPath"
