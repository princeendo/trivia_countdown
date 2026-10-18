[CmdletBinding()]
param(
    [string]$Msys2Root,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if (-not $Msys2Root) { $Msys2Root = Join-Path $root 'build\tools\msys64' }
$vendor = Join-Path $root 'build\vendor\windows'
$sourceArchive = Join-Path $root 'dist\Trivia-Countdown-FFmpeg-9.0.1-Windows-x64-sources.tar.gz'
$inputHashes = @('build_ffmpeg_windows.sh', 'compile_ffmpeg_windows.sh', 'build_ffmpeg_windows.ps1') | ForEach-Object {
    (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $_) -Algorithm SHA256).Hash
}
$inputHashes += (Get-FileHash -LiteralPath (Join-Path $root 'packaging\FFMPEG_WINDOWS_SOURCE_README.md') -Algorithm SHA256).Hash
$inputKey = $inputHashes -join ':'
$manifestPath = Join-Path $vendor 'build-manifest.json'
$outputs = @{
    ffmpeg = (Join-Path $vendor 'bin\ffmpeg.exe')
    ffprobe = (Join-Path $vendor 'bin\ffprobe.exe')
    sources = $sourceArchive
}
if (-not $Force -and (Test-Path -LiteralPath $manifestPath)) {
    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    $verified = $manifest.inputKey -eq $inputKey
    foreach ($name in $outputs.Keys) {
        if (-not (Test-Path -LiteralPath $outputs[$name])) { $verified = $false; break }
        if ((Get-FileHash -LiteralPath $outputs[$name] -Algorithm SHA256).Hash -ne $manifest.hashes.$name) { $verified = $false; break }
    }
    if ($verified) { Write-Host 'Reusing verified source-built Windows FFmpeg binaries and matching sources.'; return }
}
$bash = Join-Path $Msys2Root 'usr\bin\bash.exe'
if (-not (Test-Path -LiteralPath $bash -PathType Leaf)) {
    throw 'MSYS2 build tools are missing. Run scripts\setup_windows_ffmpeg_tools.ps1 first, or supply -Msys2Root.'
}
$previousSystem = $env:MSYSTEM
$previousScript = $env:TRIVIA_FFMPEG_BUILD_SCRIPT
try {
    $env:MSYSTEM = 'UCRT64'
    $env:TRIVIA_FFMPEG_BUILD_SCRIPT = (Join-Path $PSScriptRoot 'build_ffmpeg_windows.sh').Replace('\', '/')
    & $bash --login -c 'exec bash "$TRIVIA_FFMPEG_BUILD_SCRIPT"'
    if ($LASTEXITCODE -ne 0) { throw "Windows FFmpeg source build failed with exit code $LASTEXITCODE." }
    $hashes = @{}
    foreach ($name in $outputs.Keys) {
        $hashes[$name] = (Get-FileHash -LiteralPath $outputs[$name] -Algorithm SHA256).Hash
    }
    @{ inputKey = $inputKey; hashes = $hashes } | ConvertTo-Json | Set-Content -LiteralPath $manifestPath -Encoding ascii
} finally {
    $env:MSYSTEM = $previousSystem
    $env:TRIVIA_FFMPEG_BUILD_SCRIPT = $previousScript
}
