param(
  [string]$Python = "python",
  [string]$Node = "npm",
  [string]$Version = "0.0.0",
  [string]$Publisher = "CN=ProtoFlowDev",
  [string]$IdentityName = "ProtoFlow.Desktop",
  [string]$DisplayName = "ProtoFlow",
  [string]$PublisherDisplayName = "ProtoFlow",
  [string]$CertPassword = "ProtoFlow.Dev.123!",
  [switch]$SkipSign
)

$ErrorActionPreference = "Stop"

function Find-ToolPath {
  param(
    [Parameter(Mandatory = $true)][string]$ToolName,
    [Parameter(Mandatory = $true)][string]$ExeName
  )

  $cmd = Get-Command $ToolName -ErrorAction SilentlyContinue
  if ($cmd) {
    return $cmd.Path
  }

  $kitsRoot = Join-Path ${env:ProgramFiles(x86)} "Windows Kits\10\bin"
  if (-not (Test-Path -LiteralPath $kitsRoot)) {
    throw "Windows SDK path not found: $kitsRoot"
  }

  $candidate = Get-ChildItem -Path $kitsRoot -Filter $ExeName -Recurse -ErrorAction SilentlyContinue |
    Sort-Object FullName -Descending |
    Select-Object -First 1

  if (-not $candidate) {
    throw "$ExeName not found in Windows SDK."
  }
  return $candidate.FullName
}

function Convert-ToMsixVersion {
  param([Parameter(Mandatory = $true)][string]$RawVersion)
  $value = $RawVersion.TrimStart("v", "V")
  $parts = $value.Split(".")
  $nums = @()
  foreach ($p in $parts) {
    if ($p -match "^\d+$") {
      $nums += [int]$p
    }
    else {
      $nums += 0
    }
    if ($nums.Count -ge 4) { break }
  }
  while ($nums.Count -lt 4) { $nums += 0 }
  return "$($nums[0]).$($nums[1]).$($nums[2]).$($nums[3])"
}

function Coalesce-Setting {
  param(
    [string]$Value,
    [string]$Fallback
  )
  if ($null -ne $Value -and $Value.Trim().Length -gt 0) {
    return $Value.Trim()
  }
  return $Fallback
}

function Resize-Png {
  param(
    [Parameter(Mandatory = $true)][string]$Source,
    [Parameter(Mandatory = $true)][string]$Target,
    [Parameter(Mandatory = $true)][int]$Width,
    [Parameter(Mandatory = $true)][int]$Height
  )

  Add-Type -AssemblyName System.Drawing
  $img = [System.Drawing.Image]::FromFile($Source)
  try {
    $bmp = New-Object System.Drawing.Bitmap($Width, $Height)
    $gfx = [System.Drawing.Graphics]::FromImage($bmp)
    try {
      $gfx.Clear([System.Drawing.Color]::Transparent)
      $gfx.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
      $gfx.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
      $gfx.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality

      $scale = [Math]::Min($Width / $img.Width, $Height / $img.Height)
      $w = [int][Math]::Round($img.Width * $scale)
      $h = [int][Math]::Round($img.Height * $scale)
      $x = [int](($Width - $w) / 2)
      $y = [int](($Height - $h) / 2)
      $gfx.DrawImage($img, $x, $y, $w, $h)

      $dir = Split-Path -Parent $Target
      if (-not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
      }
      $bmp.Save($Target, [System.Drawing.Imaging.ImageFormat]::Png)
    }
    finally {
      $gfx.Dispose()
      $bmp.Dispose()
    }
  }
  finally {
    $img.Dispose()
  }
}

function Is-TrueString {
  param([string]$Value)
  if ($null -eq $Value) {
    return $false
  }
  $v = $Value.Trim().ToLowerInvariant()
  return $v -in @("1", "true", "yes", "y", "on")
}

$IdentityName = Coalesce-Setting -Value $IdentityName -Fallback "ProtoFlow.Desktop"
$Publisher = Coalesce-Setting -Value $Publisher -Fallback "CN=ProtoFlowDev"
$DisplayName = Coalesce-Setting -Value $DisplayName -Fallback "ProtoFlow"
$PublisherDisplayName = Coalesce-Setting -Value $PublisherDisplayName -Fallback "ProtoFlow"
$CertPassword = Coalesce-Setting -Value $CertPassword -Fallback "ProtoFlow.Dev.123!"
$msixVersion = Convert-ToMsixVersion -RawVersion $Version
if (-not $PSBoundParameters.ContainsKey("SkipSign")) {
  $SkipSign = Is-TrueString -Value $env:MSIX_SKIP_SIGN
}
$repoRoot = Resolve-Path "."
$distRoot = Join-Path $repoRoot "dist"
$appDist = Join-Path $distRoot "ProtoFlow"
$msixRoot = Join-Path $distRoot "msix"
$stageRoot = Join-Path $msixRoot "stage"
$assetsRoot = Join-Path $stageRoot "Assets"
$manifestTemplate = Join-Path $repoRoot "installer\msix\AppxManifest.xml.template"
$manifestPath = Join-Path $stageRoot "AppxManifest.xml"
$msixName = "ProtoFlow-$msixVersion.msix"
$msixPath = Join-Path $msixRoot $msixName

Write-Host "==> Build app payload"
& powershell -ExecutionPolicy Bypass -File ".\scripts\build_windows.ps1" -Python $Python -Node $Node

if (-not (Test-Path -LiteralPath $appDist)) {
  throw "App dist not found: $appDist"
}
if (-not (Test-Path -LiteralPath $manifestTemplate)) {
  throw "MSIX manifest template not found: $manifestTemplate"
}

Write-Host "==> Prepare MSIX staging directory"
if (Test-Path -LiteralPath $stageRoot) {
  Remove-Item -LiteralPath $stageRoot -Recurse -Force
}
if (Test-Path -LiteralPath $msixPath) {
  Remove-Item -LiteralPath $msixPath -Force
}
New-Item -ItemType Directory -Path $stageRoot | Out-Null
Copy-Item -Path (Join-Path $appDist "*") -Destination $stageRoot -Recurse -Force

Write-Host "==> Generate MSIX assets"
$logoCandidates = @(
  (Join-Path $repoRoot "ui\assets\icons\logo_mark.png"),
  (Join-Path $repoRoot "ui\assets\icons\logo.png")
)
$logoSource = $logoCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $logoSource) {
  throw "Logo source missing. Tried: $($logoCandidates -join ', ')"
}
Resize-Png -Source $logoSource -Target (Join-Path $assetsRoot "StoreLogo.png") -Width 50 -Height 50
Resize-Png -Source $logoSource -Target (Join-Path $assetsRoot "Square44x44Logo.png") -Width 44 -Height 44
Resize-Png -Source $logoSource -Target (Join-Path $assetsRoot "Square150x150Logo.png") -Width 150 -Height 150
Resize-Png -Source $logoSource -Target (Join-Path $assetsRoot "Square310x310Logo.png") -Width 310 -Height 310
Resize-Png -Source $logoSource -Target (Join-Path $assetsRoot "Wide310x150Logo.png") -Width 310 -Height 150
Resize-Png -Source $logoSource -Target (Join-Path $assetsRoot "SplashScreen.png") -Width 620 -Height 300

Write-Host "==> Render AppxManifest.xml"
$manifest = Get-Content -LiteralPath $manifestTemplate -Raw -Encoding UTF8
$manifest = $manifest.Replace("__IDENTITY_NAME__", $IdentityName)
$manifest = $manifest.Replace("__PUBLISHER__", $Publisher)
$manifest = $manifest.Replace("__VERSION__", $msixVersion)
$manifest = $manifest.Replace("__DISPLAY_NAME__", $DisplayName)
$manifest = $manifest.Replace("__PUBLISHER_DISPLAY_NAME__", $PublisherDisplayName)
Set-Content -LiteralPath $manifestPath -Value $manifest -Encoding UTF8

$makeAppx = Find-ToolPath -ToolName "makeappx" -ExeName "makeappx.exe"

Write-Host "==> Pack MSIX"
if (-not (Test-Path -LiteralPath $msixRoot)) {
  New-Item -ItemType Directory -Path $msixRoot | Out-Null
}
& $makeAppx pack /d $stageRoot /p $msixPath /o | Out-Host

if (-not (Test-Path -LiteralPath $msixPath)) {
  throw "MSIX package not generated: $msixPath"
}

if ($SkipSign) {
  Write-Host "==> Skip signing (MSIX_SKIP_SIGN=true or -SkipSign)"
  Write-Host "MSIX generated (unsigned): $msixPath"
  return
}

$signTool = Find-ToolPath -ToolName "signtool" -ExeName "signtool.exe"

$certDir = Join-Path $msixRoot "cert"
if (-not (Test-Path -LiteralPath $certDir)) {
  New-Item -ItemType Directory -Path $certDir | Out-Null
}
$certPfx = Join-Path $certDir "ProtoFlow_msix_signing.pfx"
$certCer = Join-Path $certDir "ProtoFlow_msix_signing.cer"

if ($env:MSIX_CERT_PFX_BASE64 -and $env:MSIX_CERT_PASSWORD) {
  Write-Host "==> Use provided signing certificate"
  [IO.File]::WriteAllBytes($certPfx, [Convert]::FromBase64String($env:MSIX_CERT_PFX_BASE64))
  $CertPassword = $env:MSIX_CERT_PASSWORD
}
else {
  Write-Host "==> Generate self-signed certificate for MSIX"
  $cert = New-SelfSignedCertificate -Type Custom `
    -KeyAlgorithm RSA `
    -KeyLength 2048 `
    -HashAlgorithm sha256 `
    -NotAfter (Get-Date).AddYears(3) `
    -Subject $Publisher `
    -CertStoreLocation "Cert:\CurrentUser\My" `
    -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.3")

  if (-not $cert) {
    throw "Unable to create self-signed certificate."
  }

  $securePwd = ConvertTo-SecureString -String $CertPassword -Force -AsPlainText
  Export-PfxCertificate -Cert $cert -FilePath $certPfx -Password $securePwd | Out-Null
  Export-Certificate -Cert $cert -FilePath $certCer | Out-Null
}

Write-Host "==> Sign MSIX"
$signArgs = @("sign", "/fd", "SHA256", "/f", $certPfx, "/p", $CertPassword, "/td", "SHA256")
try {
  & $signTool @($signArgs + @("/tr", "http://timestamp.digicert.com", $msixPath)) | Out-Host
}
catch {
  Write-Warning "Timestamp signing failed, retrying without timestamp."
  & $signTool @($signArgs + @($msixPath)) | Out-Host
}

Write-Host "==> Verify signature"
& $signTool verify /pa $msixPath | Out-Host

Write-Host "MSIX generated: $msixPath"
if (Test-Path -LiteralPath $certCer) {
  Write-Host "Certificate exported: $certCer"
}
