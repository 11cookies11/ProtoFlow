param(
  [string]$Source = "assets/icons/logo.png",
  [string]$Output = "installer/ProtoFlow.ico",
  [int]$Size = 256
)

if (-not (Test-Path -LiteralPath $Source)) {
  throw "Source image not found: $Source"
}

$sourceExt = [System.IO.Path]::GetExtension($Source).ToLowerInvariant()
$magick = Get-Command magick -ErrorAction SilentlyContinue

if ($magick -and $sourceExt -eq ".svg") {
  & $magick.Path $Source -resize "${Size}x${Size}" $Output | Out-Null
  if (-not (Test-Path -LiteralPath $Output)) {
    throw "Failed to generate icon via ImageMagick."
  }
  return
}

if ($sourceExt -eq ".png") {
  Add-Type -AssemblyName System.Drawing
  $img = [System.Drawing.Image]::FromFile($Source)
  $bmp = New-Object System.Drawing.Bitmap($Size, $Size)
  $gfx = [System.Drawing.Graphics]::FromImage($bmp)
  $gfx.Clear([System.Drawing.Color]::Transparent)
  $gfx.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
  $gfx.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
  $gfx.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality

  $scale = [Math]::Min($Size / $img.Width, $Size / $img.Height)
  $w = [int][Math]::Round($img.Width * $scale)
  $h = [int][Math]::Round($img.Height * $scale)
  $x = [int](($Size - $w) / 2)
  $y = [int](($Size - $h) / 2)
  $gfx.DrawImage($img, $x, $y, $w, $h)

  $icon = [System.Drawing.Icon]::FromHandle($bmp.GetHicon())
  $fs = New-Object System.IO.FileStream($Output, [System.IO.FileMode]::Create)
  $icon.Save($fs)
  $fs.Close()

  $icon.Dispose()
  $gfx.Dispose()
  $bmp.Dispose()
  $img.Dispose()
  return
}

throw "No available converter. Provide a PNG source or install ImageMagick for SVG."
