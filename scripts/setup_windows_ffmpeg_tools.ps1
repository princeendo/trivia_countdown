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
    # Use upstream's CI self-extractor. The Windows Server 2022 tar.exe can
    # stall indefinitely on the equivalent .tar.xz base archive.
    $archive = Join-Path $Destination 'msys2-base-x86_64-20260927.sfx.exe'
    $url = 'https://github.com/msys2/msys2-installer/releases/download/2026-09-27/msys2-base-x86_64-20260927.sfx.exe'
    Write-Host "Downloading pinned MSYS2 base: $url"
    Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $archive -TimeoutSec 300
    Write-Host 'Verifying the MSYS2 base archive SHA-256.'
    if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne 'ad336cccfda47758b5e15cda993fbba421115cb0b126697daef1ee4dfe37209f') {
        throw 'MSYS2 base archive checksum mismatch.'
    }
    Write-Host "Extracting MSYS2 into $Destination."
    $extractor = Start-Process -FilePath $archive -ArgumentList '-y', "-o$Destination" -WindowStyle Hidden -Wait -PassThru
    if ($extractor.ExitCode -ne 0) { throw "Could not extract the MSYS2 base archive (exit code $($extractor.ExitCode))." }
    if (-not (Test-Path -LiteralPath $bash -PathType Leaf)) { throw 'MSYS2 extraction did not create usr\bin\bash.exe.' }
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
