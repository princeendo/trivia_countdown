[CmdletBinding()]
param(
    [string]$ApplicationDirectory = (Join-Path $PSScriptRoot '..\dist\Trivia Countdown'),
    [int]$TimeoutSeconds = 180
)

$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') {
    throw 'Windows package verification must run on Windows.'
}
if ($TimeoutSeconds -le 0 -or $TimeoutSeconds -gt 3600) {
    throw 'TimeoutSeconds must be between 1 and 3600.'
}
$application = (Resolve-Path -LiteralPath (Join-Path $ApplicationDirectory 'Trivia Countdown.exe')).Path
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$reports = Join-Path $root 'build\verification'
New-Item -ItemType Directory -Force -Path $reports | Out-Null
$reportPath = Join-Path $reports ("WIN-405-{0}-{1}.json" -f (Get-Date -Format 'yyyyMMdd-HHmmss'), [guid]::NewGuid().ToString('N'))
$savedEnvironment = @{}
foreach ($name in @('PATH', 'PYTHONHOME', 'PYTHONPATH', 'TRIVIA_COUNTDOWN_SMOKE_TEST', 'TRIVIA_COUNTDOWN_SMOKE_REPORT')) {
    $savedEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
}
$process = $null

try {
    # Launch by absolute path with no system Python or FFmpeg available on PATH.
    $env:PATH = "$env:SystemRoot\System32;$env:SystemRoot"
    $env:PYTHONHOME = $null
    $env:PYTHONPATH = $null
    foreach ($name in @('python.exe', 'ffmpeg.exe', 'ffprobe.exe')) {
        if (Get-Command $name -CommandType Application -ErrorAction SilentlyContinue) {
            throw "Isolation failed: $name is still available on PATH."
        }
    }
    $env:TRIVIA_COUNTDOWN_SMOKE_TEST = 'render'
    $env:TRIVIA_COUNTDOWN_SMOKE_REPORT = $reportPath
    $process = Start-Process -FilePath $application -WorkingDirectory $reports -PassThru
    if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
        & "$env:SystemRoot\System32\taskkill.exe" /PID $process.Id /T /F | Out-Host
        throw "Packaged render timed out after $TimeoutSeconds seconds. Report path: $reportPath"
    }
    # PowerShell must explicitly wait for a windowed executable and inspect its exit code.
    $process.Refresh()
    if (Test-Path -LiteralPath $reportPath) {
        $report = Get-Content -LiteralPath $reportPath -Raw | ConvertFrom-Json
        if ($report.error) { Write-Host $report.error }
    } else {
        throw "Packaged application exited without a report (exit code $($process.ExitCode))."
    }
    if ($process.ExitCode -ne 0 -or $report.status -ne 'passed' -or -not $report.frozen -or @($report.cases).Count -ne 2) {
        throw "Packaged render verification failed. See $reportPath"
    }
    foreach ($name in @('ffmpeg', 'ffprobe')) {
        if ($report.tools.$name.version -notmatch "^$name version [0-9]+\.[0-9]+\.[0-9]+-trivia-countdown ") {
            throw "Packaged $name does not identify a source-built FFmpeg release. See $reportPath"
        }
    }
    Write-Host "Packaged preview, silent render, audio render, and decode checks passed: $reportPath"
} finally {
    if ($process) { $process.Dispose() }
    foreach ($name in $savedEnvironment.Keys) {
        [Environment]::SetEnvironmentVariable($name, $savedEnvironment[$name], 'Process')
    }
}
