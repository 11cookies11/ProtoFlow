param(
  [Parameter(Mandatory = $true)][string]$Repo,
  [Parameter(Mandatory = $true)][string]$OutputDir,
  [string]$Tag = "",
  [switch]$Latest,
  [string]$Token = "",
  [int]$RetryCount = 8,
  [int]$RetryDelaySeconds = 15
)

$ErrorActionPreference = "Stop"

function Get-AuthHeaders {
  param([string]$AccessToken)

  $headers = @{
    "Accept" = "application/vnd.github+json"
    "User-Agent" = "ProtoFlow-SkillBundle-Downloader"
  }
  if (-not [string]::IsNullOrWhiteSpace($AccessToken)) {
    $headers["Authorization"] = "Bearer $AccessToken"
  }
  return $headers
}

function Get-DownloadHeaders {
  param([string]$AccessToken)

  $headers = @{
    "Accept" = "application/octet-stream"
    "User-Agent" = "ProtoFlow-SkillBundle-Downloader"
  }
  if (-not [string]::IsNullOrWhiteSpace($AccessToken)) {
    $headers["Authorization"] = "Bearer $AccessToken"
  }
  return $headers
}

function Get-SkillIdFromExpandedBundle {
  param([string]$ExpandedPath)

  $manifestPath = Join-Path $ExpandedPath "manifest.json"
  if (-not (Test-Path -LiteralPath $manifestPath)) {
    return $null
  }
  $manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
  if ($null -eq $manifest -or [string]::IsNullOrWhiteSpace($manifest.id)) {
    return $null
  }
  return [string]$manifest.id
}

$repo = $Repo.Trim()
$tag = $Tag.Trim()
$targetRoot = [System.IO.Path]::GetFullPath($OutputDir)

if ([string]::IsNullOrWhiteSpace($repo)) {
  throw "Repo is required."
}
if (-not $Latest -and [string]::IsNullOrWhiteSpace($tag)) {
  throw "Tag is required when -Latest is not specified."
}

if (Test-Path -LiteralPath $targetRoot) {
  Remove-Item -LiteralPath $targetRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $targetRoot -Force | Out-Null

$apiHeaders = Get-AuthHeaders -AccessToken $Token
$downloadHeaders = Get-DownloadHeaders -AccessToken $Token
$releaseApi = if ($Latest) {
  "https://api.github.com/repos/$repo/releases/latest"
}
else {
  "https://api.github.com/repos/$repo/releases/tags/$tag"
}
$releaseLabel = if ($Latest) { "$repo@latest" } else { "$repo@$tag" }

$release = $null
for ($attempt = 1; $attempt -le [Math]::Max(1, $RetryCount); $attempt++) {
  Write-Host "==> Query SkillForge release: $releaseApi (attempt $attempt/$RetryCount)"
  try {
    $release = Invoke-RestMethod -Uri $releaseApi -Headers $apiHeaders -Method Get
    if ($null -ne $release) {
      break
    }
  }
  catch {
    if ($attempt -ge $RetryCount) {
      throw
    }
    Start-Sleep -Seconds ([Math]::Max(1, $RetryDelaySeconds))
  }
}
if ($null -eq $release) {
  throw "Release not found after retries: $releaseLabel"
}

$assets = @($release.assets) | Where-Object {
  $_ -and
  $_.name -and
  $_.name -like "*.zip" -and
  $_.name -notlike "Source code*"
}

if (-not $assets.Count) {
  throw "No skill bundle zip assets found in $releaseLabel"
}

$downloadRoot = Join-Path $targetRoot "_downloads"
$expandRoot = Join-Path $targetRoot "_expanded"
New-Item -ItemType Directory -Path $downloadRoot -Force | Out-Null
New-Item -ItemType Directory -Path $expandRoot -Force | Out-Null

foreach ($asset in $assets) {
  $zipPath = Join-Path $downloadRoot $asset.name
  $tempExpand = Join-Path $expandRoot ([System.IO.Path]::GetFileNameWithoutExtension($asset.name))
  Write-Host "==> Download asset: $($asset.name)"
  Invoke-WebRequest -Uri $asset.url -Headers $downloadHeaders -OutFile $zipPath

  if (Test-Path -LiteralPath $tempExpand) {
    Remove-Item -LiteralPath $tempExpand -Recurse -Force
  }
  Expand-Archive -LiteralPath $zipPath -DestinationPath $tempExpand -Force

  $skillId = Get-SkillIdFromExpandedBundle -ExpandedPath $tempExpand
  if ([string]::IsNullOrWhiteSpace($skillId)) {
    $skillId = [System.IO.Path]::GetFileNameWithoutExtension($asset.name)
  }
  $bundleTarget = Join-Path $targetRoot $skillId
  if (Test-Path -LiteralPath $bundleTarget) {
    Remove-Item -LiteralPath $bundleTarget -Recurse -Force
  }
  New-Item -ItemType Directory -Path $bundleTarget -Force | Out-Null
  Copy-Item -Path (Join-Path $tempExpand "*") -Destination $bundleTarget -Recurse -Force
  Write-Host "Prepared bundle: $skillId"
}

Remove-Item -LiteralPath $downloadRoot -Recurse -Force
Remove-Item -LiteralPath $expandRoot -Recurse -Force

Write-Host "Prepared $($assets.Count) bundle archive(s) into $targetRoot"
