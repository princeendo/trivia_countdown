[CmdletBinding()]
param(
    [string]$Destination = (Join-Path $PSScriptRoot "..\build\vendor\windows"),
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$version = "9.0.1"
$archiveName = "ffmpeg-$version-essentials_build.zip"
$url = "https://github.com/GyanD/codexffmpeg/releases/download/$version/$archiveName"
$expectedHash = "fec81ae03971d9dd4be3ebe02e263bd2ec1d789483f931bdba5f5715e65da2e9"
$temporaryArchive = Join-Path ([System.IO.Path]::GetTempPath()) $archiveName
$temporaryDirectory = Join-Path ([System.IO.Path]::GetTempPath()) "trivia-countdown-ffmpeg-$version"

if ((Test-Path -LiteralPath $Destination) -and -not $Force) {
    $ffmpeg = Join-Path $Destination "bin\ffmpeg.exe"
    $ffprobe = Join-Path $Destination "bin\ffprobe.exe"
    if ((Test-Path -LiteralPath $ffmpeg) -and (Test-Path -LiteralPath $ffprobe)) {
        return
    }
}

Remove-Item -LiteralPath $temporaryArchive -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $temporaryDirectory -Recurse -Force -ErrorAction SilentlyContinue
Invoke-WebRequest -Uri $url -OutFile $temporaryArchive

$actualHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $temporaryArchive).Hash.ToLowerInvariant()
if ($actualHash -ne $expectedHash) {
    throw "FFmpeg archive hash mismatch. Expected $expectedHash but received $actualHash."
}

Expand-Archive -LiteralPath $temporaryArchive -DestinationPath $temporaryDirectory
$packageDirectory = Get-ChildItem -LiteralPath $temporaryDirectory -Directory | Select-Object -First 1
if ($null -eq $packageDirectory) {
    throw "The FFmpeg archive did not contain a package directory."
}

$sourceBin = Join-Path $packageDirectory.FullName "bin"
$sourceFfmpeg = Join-Path $sourceBin "ffmpeg.exe"
$sourceFfprobe = Join-Path $sourceBin "ffprobe.exe"
if (-not (Test-Path -LiteralPath $sourceFfmpeg) -or -not (Test-Path -LiteralPath $sourceFfprobe)) {
    throw "The FFmpeg archive did not contain ffmpeg.exe and ffprobe.exe."
}

Remove-Item -LiteralPath $Destination -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path (Join-Path $Destination "bin") -Force | Out-Null
Copy-Item -LiteralPath $sourceFfmpeg -Destination (Join-Path $Destination "bin\ffmpeg.exe")
Copy-Item -LiteralPath $sourceFfprobe -Destination (Join-Path $Destination "bin\ffprobe.exe")
Copy-Item -LiteralPath (Join-Path $packageDirectory.FullName "LICENSE") -Destination $Destination

& (Join-Path $Destination "bin\ffmpeg.exe") -hide_banner -version
& (Join-Path $Destination "bin\ffprobe.exe") -hide_banner -version
$encoders = & (Join-Path $Destination "bin\ffmpeg.exe") -hide_banner -encoders 2>&1
if ($encoders -notmatch "libx264" -or $encoders -notmatch "aac") {
    throw "The pinned FFmpeg build does not provide the required libx264 and AAC encoders."
}

Remove-Item -LiteralPath $temporaryArchive -Force
Remove-Item -LiteralPath $temporaryDirectory -Recurse -Force
