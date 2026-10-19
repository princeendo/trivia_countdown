[CmdletBinding()]
param(
    [string]$ApplicationDirectory = (Join-Path $PSScriptRoot '..\dist\Trivia Countdown'),
    [string]$MakeAppxPath
)

$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'MSIX packaging must run on Windows with the Windows SDK installed.' }
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

function Invoke-MsixCommand {
    param([string]$Command, [string[]]$Arguments)
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Command failed with exit code $LASTEXITCODE." }
}

if (-not $MakeAppxPath) {
    $sdk = Join-Path ${env:ProgramFiles(x86)} 'Windows Kits\10\bin'
    if (Test-Path -LiteralPath $sdk -PathType Container) {
        $MakeAppxPath = Get-ChildItem -LiteralPath $sdk -Directory |
            Where-Object { $_.Name -match '^10\.0\.\d+\.0$' } |
            Sort-Object { [version]$_.Name } -Descending |
            ForEach-Object { Join-Path $_.FullName 'x64\makeappx.exe' } |
            Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } |
            Select-Object -First 1
    }
}
if (-not $MakeAppxPath -or -not (Test-Path -LiteralPath $MakeAppxPath -PathType Leaf)) {
    throw 'Windows SDK x64 MakeAppx.exe was not found. Install the Windows SDK or pass -MakeAppxPath.'
}
$MakeAppxPath = (Resolve-Path -LiteralPath $MakeAppxPath).Path
Write-Host "Using Windows SDK MakeAppx: $MakeAppxPath"
$ApplicationDirectory = (Resolve-Path -LiteralPath $ApplicationDirectory).Path

Push-Location -LiteralPath $root
try {
    $versions = (Invoke-MsixCommand uv @('run', '--frozen', 'python', 'scripts/windows_msix.py', 'versions')) | ConvertFrom-Json
    $package = Join-Path $root "dist\Trivia-Countdown-$($versions.package)-Windows-x64.msix"
    $checksums = Join-Path $root "dist\Trivia-Countdown-$($versions.package)-Windows-x64-MSIX-SHA256SUMS.txt"
    # A failed rebuild must not leave a successful-looking previous package or checksums.
    Remove-Item -LiteralPath $package, $checksums -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath (Join-Path $root 'build\verification\STORE-002-msix.json') -Force -ErrorAction SilentlyContinue
    Invoke-MsixCommand uv @('run', '--frozen', 'python', 'scripts/windows_msix.py', 'stage', '--application-directory', $ApplicationDirectory)
    $stage = Join-Path $root 'build\windows\msix'
    & (Join-Path $PSScriptRoot 'verify_windows_package.ps1') -ApplicationDirectory (Join-Path $stage 'app')
    # Keep schema and semantic validation enabled; /nv must not be used.
    Invoke-MsixCommand $MakeAppxPath @('pack', '/o', '/h', 'SHA256', '/d', $stage, '/p', $package)
    Invoke-MsixCommand uv @('run', '--frozen', 'python', 'scripts/windows_msix.py', 'verify', '--package', $package)
    $sources = Join-Path $root 'dist\Trivia-Countdown-FFmpeg-9.0.1-Windows-x64-sources.tar.gz'
    Get-FileHash -Algorithm SHA256 -LiteralPath $package, $sources |
        ForEach-Object { '{0} *{1}' -f $_.Hash.ToLowerInvariant(), (Split-Path -Leaf $_.Path) } |
        Set-Content -Encoding ascii -LiteralPath $checksums
    Write-Host "Unsigned Store upload package: $package"
    Write-Host 'Installed MSIX qualification and Windows App Certification Kit checks are still required.'
} finally {
    Pop-Location
}
