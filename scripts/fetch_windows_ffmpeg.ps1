[CmdletBinding()]
param(
    [string]$Destination,
    [switch]$Force,
    [string]$Msys2Root
)

# Compatibility entry point. Windows packaging now uses reviewed source builds,
# never downloads a third-party FFmpeg binary with an unknown source closure.
$ErrorActionPreference = 'Stop'
if (-not $Destination) { $Destination = Join-Path $PSScriptRoot '..\build\vendor\windows' }
& (Join-Path $PSScriptRoot 'build_ffmpeg_windows.ps1') -Msys2Root $Msys2Root -Force:$Force
$source = (Resolve-Path (Join-Path $PSScriptRoot '..\build\vendor\windows')).Path
$target = [System.IO.Path]::GetFullPath($Destination)
if ($source -ine $target.TrimEnd('\')) {
    New-Item -ItemType Directory -Path (Join-Path $target 'bin') -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $source 'bin\ffmpeg.exe'), (Join-Path $source 'bin\ffprobe.exe') -Destination (Join-Path $target 'bin')
    Copy-Item -LiteralPath (Join-Path $source 'LICENSE'), (Join-Path $source 'SOURCES.txt') -Destination $target
    Copy-Item -LiteralPath (Join-Path $source 'licenses') -Destination $target -Recurse -Force
}
