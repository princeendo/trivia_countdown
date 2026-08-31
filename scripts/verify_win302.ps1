[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$UncTestRoot,

    [Parameter(Mandatory)]
    [string]$LongPathTestRoot
)

$ErrorActionPreference = "Stop"

function Assert-WritableDirectory {
    param(
        [string]$Path,
        [string]$Description
    )

    New-Item -ItemType Directory -Force -Path $Path | Out-Null
    $probePath = Join-Path $Path ".trivia-countdown-write-probe-$PID"
    try {
        [System.IO.File]::WriteAllText($probePath, "WIN-302 verification probe")
    } finally {
        Remove-Item -LiteralPath $probePath -Force -ErrorAction SilentlyContinue
    }
    Write-Host "$Description is writable: $Path"
}

function Invoke-UnitTest {
    param(
        [string]$TestName,
        [switch]$RequireExecution
    )

    Write-Host "`nRunning $TestName"
    # cmd.exe merges unittest diagnostics into text before PowerShell handles them.
    $testOutput = & cmd.exe /d /c "uv run python -m unittest -v $TestName 2>&1"
    $exitCode = $LASTEXITCODE
    $testOutput | Out-Host
    if ($exitCode -ne 0) {
        throw "$TestName failed with exit code $exitCode."
    }
    if ($RequireExecution -and (($testOutput | Out-String) -match "\bskipped\b")) {
        throw "$TestName was skipped instead of executed. Check the supplied test root."
    }
}

if ($env:OS -ne "Windows_NT") {
    throw "WIN-302 verification must run in Windows PowerShell."
}
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv was not found on PATH. Install uv, open a new PowerShell window, and retry."
}
if ($UncTestRoot -notmatch '^\\\\[^\\]+\\[^\\]+') {
    throw "UncTestRoot must be a UNC path such as \\server\share\win302."
}
if ($LongPathTestRoot -notmatch '^[A-Za-z]:\\') {
    throw "LongPathTestRoot must be an absolute local drive path such as C:\win302."
}

$longPathsEnabled = (Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem").LongPathsEnabled
if ($longPathsEnabled -ne 1) {
    throw "Windows long paths are disabled. Enable LongPathsEnabled, restart Windows, and rerun this script."
}

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$driveTempRoot = Join-Path ([System.IO.Path]::GetTempPath()) "trivia-countdown-WIN302"
if ($driveTempRoot -notmatch '^[A-Za-z]:\\') {
    throw "The system temporary directory must use a drive-letter path; received: $driveTempRoot"
}

Assert-WritableDirectory -Path $UncTestRoot -Description "UNC test root"
Assert-WritableDirectory -Path $LongPathTestRoot -Description "Long-path test root"
Assert-WritableDirectory -Path $driveTempRoot -Description "Drive-letter temporary root"

$verificationDirectory = Join-Path $root "build\verification"
New-Item -ItemType Directory -Force -Path $verificationDirectory | Out-Null
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$reportPath = Join-Path $verificationDirectory "WIN-302-$timestamp.log"

Start-Transcript -LiteralPath $reportPath -Force | Out-Null
try {
    Write-Host "WIN-302 verification report: $reportPath"
    Write-Host "UNC test root: $UncTestRoot"
    Write-Host "Long-path test root: $LongPathTestRoot"
    Write-Host "Long paths enabled: $longPathsEnabled"

    & (Join-Path $PSScriptRoot "fetch_windows_ffmpeg.ps1") -Force

    $ffmpegBin = (Resolve-Path (Join-Path $root "build\vendor\windows\bin")).Path
    $env:Path = "$ffmpegBin;$env:Path"
    $env:TEMP = $driveTempRoot
    $env:TMP = $driveTempRoot
    $env:TRIVIA_COUNTDOWN_UNC_TEST_ROOT = $UncTestRoot
    $env:TRIVIA_COUNTDOWN_LONG_PATH_TEST_ROOT = $LongPathTestRoot

    $ffmpegCommands = @(Get-Command ffmpeg -CommandType Application)
    $ffprobeCommands = @(Get-Command ffprobe -CommandType Application)
    $resolvedFfmpeg = (Resolve-Path $ffmpegCommands[0].Path).Path
    $resolvedFfprobe = (Resolve-Path $ffprobeCommands[0].Path).Path
    if ($resolvedFfmpeg -ine (Join-Path $ffmpegBin "ffmpeg.exe") -or
        $resolvedFfprobe -ine (Join-Path $ffmpegBin "ffprobe.exe")) {
        throw "Tests are not using the fetched pinned FFmpeg tools."
    }

    & "$ffmpegBin\ffmpeg.exe" -hide_banner -version
    & "$ffmpegBin\ffprobe.exe" -hide_banner -version

    uv sync --frozen
    if ($LASTEXITCODE -ne 0) {
        throw "uv sync --frozen failed with exit code $LASTEXITCODE."
    }

    Invoke-UnitTest -TestName "tests.test_app"
    Invoke-UnitTest -TestName "tests.test_app.VideoIntegrationTests.test_special_paths_render_with_relative_overlay_directory" -RequireExecution
    Invoke-UnitTest -TestName "tests.test_app.VideoIntegrationTests.test_configured_unc_path_render" -RequireExecution
    Invoke-UnitTest -TestName "tests.test_app.VideoIntegrationTests.test_configured_long_path_render" -RequireExecution
    Invoke-UnitTest -TestName "tests.test_app.RenderServiceTests.test_failed_composition_preserves_existing_output"
    Invoke-UnitTest -TestName "tests.test_app.RenderServiceTests.test_composition_reports_locked_output_and_preserves_existing_file"

    Write-Host "`nWIN-302 verification passed. Share this report for review: $reportPath"
} finally {
    Stop-Transcript | Out-Null
}
