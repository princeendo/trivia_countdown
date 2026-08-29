[CmdletBinding()]
param(
    [string]$IsccPath
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
& (Join-Path $PSScriptRoot "fetch_windows_ffmpeg.ps1")
& (Join-Path $PSScriptRoot "collect_runtime_licenses.ps1")
uv sync --group build --frozen
uv run python (Join-Path $PSScriptRoot "create_windows_icon.py")
uv run pyinstaller --noconfirm --clean --workpath (Join-Path $root "build\pyinstaller") (Join-Path $root "packaging\TriviaCountdownWindows.spec")

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

$version = uv run --frozen python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])"
& $IsccPath "/DAppVersion=$version" (Join-Path $root "packaging\TriviaCountdown.iss")

$installer = Join-Path $root "dist\Trivia-Countdown-$version-Windows-x64-Setup.exe"
if (-not (Test-Path -LiteralPath $installer -PathType Leaf)) {
    throw "Inno Setup did not create the expected installer: $installer"
}
Get-FileHash -Algorithm SHA256 -LiteralPath $installer |
    ForEach-Object { "{0} *{1}" -f $_.Hash.ToLowerInvariant(), (Split-Path -Leaf $_.Path) } |
    Set-Content -Encoding ascii (Join-Path $root "dist\Trivia-Countdown-$version-Windows-x64-SHA256SUMS.txt")
