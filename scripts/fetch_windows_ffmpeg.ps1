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
$expectedExecutableHashes = @{
    "ffmpeg.exe" = "72a489eccd008c2ec2c0a5856c5c75bc3d8bbfa90166c4566865c246445e6aa3"
    "ffprobe.exe" = "19202b23c0043f15ad1b7bce2344f406fd52bd6efd8f995ce02e7392a1cec52f"
}
$temporaryArchive = Join-Path ([System.IO.Path]::GetTempPath()) $archiveName
$temporaryDirectory = Join-Path ([System.IO.Path]::GetTempPath()) "trivia-countdown-ffmpeg-$version"

function Assert-VerifiedExecutable {
    param(
        [string]$Path,
        [string]$ExpectedHash
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Expected executable is missing: $Path"
    }
    $actualHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
    if ($actualHash -ne $ExpectedHash) {
        throw "Executable hash mismatch for $Path. Expected $ExpectedHash but received $actualHash."
    }

    $stream = [System.IO.File]::OpenRead($Path)
    try {
        $dosHeader = [byte[]]::new(64)
        if ($stream.Read($dosHeader, 0, $dosHeader.Length) -ne $dosHeader.Length -or
            $dosHeader[0] -ne 0x4d -or $dosHeader[1] -ne 0x5a) {
            throw "Expected a PE executable: $Path"
        }
        $peHeaderOffset = [System.BitConverter]::ToInt32($dosHeader, 0x3c)
        if ($peHeaderOffset -lt 0 -or $peHeaderOffset + 6 -gt $stream.Length) {
            throw "Invalid PE header in $Path"
        }
        $stream.Position = $peHeaderOffset
        $peHeader = [byte[]]::new(6)
        if ($stream.Read($peHeader, 0, $peHeader.Length) -ne $peHeader.Length -or
            $peHeader[0] -ne 0x50 -or $peHeader[1] -ne 0x45) {
            throw "Invalid PE header in $Path"
        }
        $machine = [System.BitConverter]::ToUInt16($peHeader, 4)
    } finally {
        $stream.Dispose()
    }
    if ($machine -ne 0x8664) {
        throw "Expected an x64 executable but found PE machine type 0x$($machine.ToString('X4')): $Path"
    }
}

if ((Test-Path -LiteralPath $Destination) -and -not $Force) {
    $ffmpeg = Join-Path $Destination "bin\ffmpeg.exe"
    $ffprobe = Join-Path $Destination "bin\ffprobe.exe"
    if ((Test-Path -LiteralPath $ffmpeg) -and (Test-Path -LiteralPath $ffprobe)) {
        Assert-VerifiedExecutable -Path $ffmpeg -ExpectedHash $expectedExecutableHashes["ffmpeg.exe"]
        Assert-VerifiedExecutable -Path $ffprobe -ExpectedHash $expectedExecutableHashes["ffprobe.exe"]
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
Assert-VerifiedExecutable -Path $sourceFfmpeg -ExpectedHash $expectedExecutableHashes["ffmpeg.exe"]
Assert-VerifiedExecutable -Path $sourceFfprobe -ExpectedHash $expectedExecutableHashes["ffprobe.exe"]

Remove-Item -LiteralPath $Destination -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path (Join-Path $Destination "bin") -Force | Out-Null
Copy-Item -LiteralPath $sourceFfmpeg -Destination (Join-Path $Destination "bin\ffmpeg.exe")
Copy-Item -LiteralPath $sourceFfprobe -Destination (Join-Path $Destination "bin\ffprobe.exe")
Copy-Item -LiteralPath (Join-Path $packageDirectory.FullName "LICENSE") -Destination $Destination
Assert-VerifiedExecutable -Path (Join-Path $Destination "bin\ffmpeg.exe") -ExpectedHash $expectedExecutableHashes["ffmpeg.exe"]
Assert-VerifiedExecutable -Path (Join-Path $Destination "bin\ffprobe.exe") -ExpectedHash $expectedExecutableHashes["ffprobe.exe"]

& (Join-Path $Destination "bin\ffmpeg.exe") -hide_banner -version
& (Join-Path $Destination "bin\ffprobe.exe") -hide_banner -version
$encoders = & (Join-Path $Destination "bin\ffmpeg.exe") -hide_banner -encoders 2>&1
if (-not ($encoders -match "libx264") -or -not ($encoders -match "aac")) {
    throw "The pinned FFmpeg build does not provide the required libx264 and AAC encoders."
}

Remove-Item -LiteralPath $temporaryArchive -Force
Remove-Item -LiteralPath $temporaryDirectory -Recurse -Force
