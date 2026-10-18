[CmdletBinding()]
param(
    [string]$IsccPath,
    [string]$Msys2Root
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not $Msys2Root) { $Msys2Root = Join-Path $root 'build\tools\msys64' }

function Invoke-BuildCommand {
    param([string]$Command, [string[]]$Arguments)
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Command failed with exit code $LASTEXITCODE."
    }
}

if (-not $IsccPath) {
    $command = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($command) {
        $IsccPath = $command.Source
    } else {
        $IsccPath = "${env:ProgramFiles(x86)}\Inno Setup 7\ISCC.exe"
    }
}
if (-not (Test-Path -LiteralPath $IsccPath -PathType Leaf)) {
    throw "Inno Setup 7.1.0 was not found. Install it or pass -IsccPath with the full path to ISCC.exe."
}
$IsccPath = (Resolve-Path -LiteralPath $IsccPath).Path

Push-Location -LiteralPath $root
try {
    & (Join-Path $PSScriptRoot 'build_ffmpeg_windows.ps1') -Msys2Root $Msys2Root
    & (Join-Path $PSScriptRoot "collect_runtime_licenses.ps1")
    Invoke-BuildCommand uv @('sync', '--group', 'build', '--frozen')
    Invoke-BuildCommand uv @('run', 'python', (Join-Path $PSScriptRoot 'create_windows_icon.py'))
    Invoke-BuildCommand uv @('run', 'pyinstaller', '--noconfirm', '--clean', '--workpath', (Join-Path $root 'build\pyinstaller'), (Join-Path $root 'packaging\TriviaCountdownWindows.spec'))
    & (Join-Path $PSScriptRoot 'verify_windows_package.ps1')

    $version = Invoke-BuildCommand uv @('run', '--frozen', 'python', '-c', "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])")
    Invoke-BuildCommand $IsccPath @("/DAppVersion=$version", (Join-Path $root 'packaging\TriviaCountdown.iss'))

    $installer = Join-Path $root "dist\Trivia-Countdown-$version-Windows-x64-Setup.exe"
    if (-not (Test-Path -LiteralPath $installer -PathType Leaf)) {
        throw "Inno Setup did not create the expected installer: $installer"
    }
    $sources = Join-Path $root 'dist\Trivia-Countdown-FFmpeg-9.0.1-Windows-x64-sources.tar.gz'
    Get-FileHash -Algorithm SHA256 -LiteralPath $installer, $sources |
        ForEach-Object { "{0} *{1}" -f $_.Hash.ToLowerInvariant(), (Split-Path -Leaf $_.Path) } |
        Set-Content -Encoding ascii (Join-Path $root "dist\Trivia-Countdown-$version-Windows-x64-SHA256SUMS.txt")
} finally {
    Pop-Location
}
