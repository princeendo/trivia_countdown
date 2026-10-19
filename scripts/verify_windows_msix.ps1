[CmdletBinding()]
param([ValidateRange(1, 3600)][int]$TimeoutSeconds = 180)

$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT' -or $PSVersionTable.PSEdition -ne 'Desktop') {
    throw 'Run installed MSIX verification in Windows PowerShell 5.1 on Windows 10/11 x64.'
}
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$packages = @(Get-AppxPackage -Name 'ColinWhite.TriviaCountdown')
if ($packages.Count -ne 1) { throw 'Install exactly one Trivia Countdown MSIX for the current user first.' }
$package = $packages[0]
if ($package.Publisher -cne 'CN=49A512EA-D5D6-441A-8499-B44017F81C7D' -or $package.Architecture -ne 'X64') {
    throw 'Installed MSIX publisher or architecture does not match the Store product.'
}
$reports = Join-Path $root 'build\verification'
New-Item -ItemType Directory -Force -Path $reports | Out-Null
$resultPath = Join-Path $reports ("STORE-003-{0}-{1}.json" -f (Get-Date -Format 'yyyyMMdd-HHmmss'), [guid]::NewGuid().ToString('N'))
$logPath = [IO.Path]::ChangeExtension($resultPath, '.log')
$verifier = (Join-Path $PSScriptRoot 'verify_windows_package.ps1').Replace("'", "''")
$application = (Join-Path $package.InstallLocation 'app').Replace("'", "''")
$fullName = $package.PackageFullName.Replace("'", "''")
$quotedResult = $resultPath.Replace("'", "''")
$quotedLog = $logPath.Replace("'", "''")
# Invoke-CommandInDesktopPackage does not wait or expose the child's exit code.
# The worker runs the existing timed verifier and writes an atomic completion report.
$worker = @"
`$ErrorActionPreference = 'Stop'
`$result = @{ status = 'failed'; package_full_name = '$fullName'; scope = 'installed-package-context-smoke' }
try {
    & '$verifier' -ApplicationDirectory '$application' -ExpectedPackageFullName '$fullName' -TimeoutSeconds $TimeoutSeconds *> '$quotedLog'
    `$result.status = 'passed'
} catch {
    `$result.error = `$_.Exception.Message
} finally {
    `$result | ConvertTo-Json | Set-Content -Encoding utf8 -LiteralPath '$quotedResult.tmp'
    Move-Item -LiteralPath '$quotedResult.tmp' -Destination '$quotedResult'
}
"@
$encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($worker))
Invoke-CommandInDesktopPackage -PackageFamilyName $package.PackageFamilyName -AppId 'TriviaCountdown' `
    -Command "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" `
    -Args "-NoProfile -NonInteractive -EncodedCommand $encoded" -PreventBreakaway
$deadline = (Get-Date).AddSeconds($TimeoutSeconds + 60)
while (-not (Test-Path -LiteralPath $resultPath)) {
    if ((Get-Date) -gt $deadline) { throw "Installed MSIX verifier timed out. Inspect $logPath" }
    Start-Sleep -Milliseconds 500
}
$result = Get-Content -LiteralPath $resultPath -Raw | ConvertFrom-Json
Get-Content -LiteralPath $logPath | Write-Host
if ($result.status -ne 'passed') { throw "Installed MSIX checks failed: $($result.error). See $resultPath" }
Write-Host "Installed MSIX identity, preview, audio/silent render, and decode checks passed: $resultPath"
Write-Host 'Start-menu activation, dialogs, visual/DPI, playback, upgrade/uninstall, and WACK still need live qualification.'
