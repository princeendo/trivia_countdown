[CmdletBinding()]
param(
    [string]$Destination
)

$ErrorActionPreference = 'Stop'
if (-not $Destination) { $Destination = Join-Path $PSScriptRoot '..\build\tools' }
if ($env:OS -ne 'Windows_NT') { throw 'The Windows FFmpeg toolchain requires Windows x64.' }
New-Item -ItemType Directory -Path $Destination -Force | Out-Null
$Destination = (Resolve-Path -LiteralPath $Destination).Path
if ($Destination -match "[\s']") { throw 'MSYS2 must be installed at a path without spaces or apostrophes.' }
$bash = Join-Path $Destination 'msys64\usr\bin\bash.exe'
if (-not (Test-Path -LiteralPath $bash)) {
    $archive = Join-Path $Destination 'msys2-base-x86_64-20260927.tar.xz'
    $url = 'https://github.com/msys2/msys2-installer/releases/download/2026-09-27/msys2-base-x86_64-20260927.tar.xz'
    Write-Host "Downloading pinned MSYS2 base: $url"
    Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $archive -TimeoutSec 300
    Write-Host 'Verifying the MSYS2 base archive SHA-256.'
    if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne 'ea2f31a0b6ade63914ce441ffb022f0f6aa96982bfefa2326460a26d5fb01322') {
        throw 'MSYS2 base archive checksum mismatch.'
    }
    Write-Host "Extracting MSYS2 into $Destination."
    & tar.exe -xf $archive -C $Destination
    if ($LASTEXITCODE -ne 0) { throw 'Could not extract the MSYS2 base archive.' }
}
$previous = $env:MSYSTEM
try {
    $env:MSYSTEM = 'UCRT64'
    # Initialize the keyring/profile separately, as recommended by MSYS2's CI
    # instructions, so first-run failures are distinct from package updates.
    # A second update is needed after updates to the MSYS2 runtime itself.
    foreach ($command in @(
        ' ',
        'pacman -Syu --noconfirm',
        'pacman -Syu --noconfirm',
        'pacman -S --needed --noconfirm make diffutils git mingw-w64-ucrt-x86_64-gcc mingw-w64-ucrt-x86_64-nasm mingw-w64-ucrt-x86_64-pkgconf'
    )) {
        Write-Host "Running MSYS2 setup command: $command"
        & $bash --login -c $command
        if ($LASTEXITCODE -ne 0) { throw "MSYS2 toolchain setup failed: $command" }
    }
    Write-Host "Windows FFmpeg build tools ready: $(Join-Path $Destination 'msys64')"
} finally {
    $env:MSYSTEM = $previous
}
