param([switch]$RebuildDesktop)

$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $taskRoot

if ($RebuildDesktop) {
    & (Join-Path $PSScriptRoot 'build_desktop.ps1')
    if ($LASTEXITCODE -ne 0) { throw 'Desktop build failed.' }
}

$taskExe = Join-Path $taskRoot 'deliverables\desktop\Estimate2\Estimate2.exe'
if (-not (Test-Path -LiteralPath $taskExe)) {
    throw 'Desktop executable is missing. Run scripts\setup.ps1 and scripts\build_desktop.ps1 first.'
}

$taskCompilerCandidates = @((Get-Command 'ISCC.exe' -ErrorAction SilentlyContinue).Source)
if ($env:LOCALAPPDATA) {
    $taskCompilerCandidates += Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'
}
foreach ($taskBase in @($env:LOCALAPPDATA, ${env:ProgramFiles(x86)}, $env:ProgramFiles)) {
    if ($taskBase) { $taskCompilerCandidates += Join-Path $taskBase 'Inno Setup 6\ISCC.exe' }
}
$taskCompiler = $taskCompilerCandidates | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
if (-not $taskCompiler) {
    throw 'Inno Setup 6 is required. Install it with: winget install --id JRSoftware.InnoSetup --exact --scope user'
}

& $taskCompiler (Join-Path $taskRoot 'installer\EstimateDesktop.iss')
if ($LASTEXITCODE -ne 0) { throw 'Installer build failed.' }

$taskInstaller = Join-Path $taskRoot 'deliverables\EstimateDesktop-Setup-1.0.0.exe'
if (-not (Test-Path -LiteralPath $taskInstaller)) { throw 'Installer was not created.' }
Write-Output "Installer: $taskInstaller"
