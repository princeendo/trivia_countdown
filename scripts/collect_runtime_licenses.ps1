[CmdletBinding()]
param(
    [string]$Destination = (Join-Path $PSScriptRoot "..\build\vendor\licenses")
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
uv sync --group build --frozen
if ($LASTEXITCODE -ne 0) { throw "Could not install the locked build dependencies." }

$pythonLicense = uv run python -c "from pathlib import Path; import sys; print(Path(sys.base_prefix) / 'LICENSE.txt')"
if ($LASTEXITCODE -ne 0) { throw "Could not locate the Python license." }
$pillowLicense = uv run python -c "import importlib.metadata as metadata; print(metadata.distribution('Pillow')._path / 'licenses' / 'LICENSE')"
if ($LASTEXITCODE -ne 0) { throw "Could not locate the Pillow license." }
$pyinstallerLicense = uv run python -c "import importlib.metadata as metadata; print(metadata.distribution('pyinstaller')._path / 'licenses' / 'COPYING.txt')"
if ($LASTEXITCODE -ne 0) { throw "Could not locate the PyInstaller license." }
$fontLicense = Join-Path $root "assets\fonts\LICENSE.txt"
$ffmpegLicense = Join-Path $root "build\vendor\windows\LICENSE"

foreach ($licenseFile in @($pythonLicense, $pillowLicense, $pyinstallerLicense, $fontLicense, $ffmpegLicense)) {
    if (-not (Test-Path -LiteralPath $licenseFile -PathType Leaf)) {
        throw "Runtime license not found: $licenseFile"
    }
}

New-Item -ItemType Directory -Path $Destination -Force | Out-Null
Copy-Item -LiteralPath $pythonLicense -Destination (Join-Path $Destination "PYTHON-LICENSE.txt")
Copy-Item -LiteralPath $pillowLicense -Destination (Join-Path $Destination "PILLOW-AND-NATIVE-LIBRARIES-LICENSE.txt")
Copy-Item -LiteralPath $pyinstallerLicense -Destination (Join-Path $Destination "PYINSTALLER-LICENSE.txt")
Copy-Item -LiteralPath $fontLicense -Destination (Join-Path $Destination "NOTO-SANS-OFL-1.1.txt")
Copy-Item -LiteralPath $ffmpegLicense -Destination (Join-Path $Destination "FFMPEG-LICENSE.txt")
$windowsLicenses = Join-Path $Destination 'windows-ffmpeg'
New-Item -ItemType Directory -Path $windowsLicenses -Force | Out-Null
Copy-Item -Path (Join-Path $root 'build\vendor\windows\licenses\*') -Destination $windowsLicenses -Recurse -Force
Copy-Item -LiteralPath (Join-Path $root "packaging\licenses\TCL-LICENSE.txt") -Destination (Join-Path $Destination "TCL-LICENSE.txt")
Copy-Item -LiteralPath (Join-Path $root "packaging\licenses\TK-LICENSE.txt") -Destination (Join-Path $Destination "TK-LICENSE.txt")
