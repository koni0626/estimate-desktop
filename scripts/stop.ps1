$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskEscapedRoot = [regex]::Escape($taskRoot)
# Only stop processes whose command line belongs to this workspace.
Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -and $_.CommandLine -match $taskEscapedRoot -and
    (($_.Name -eq 'python.exe' -and $_.CommandLine -match 'uvicorn backend\.app\.main:app') -or
     ($_.Name -eq 'node.exe' -and $_.CommandLine -match 'vite[\\/]bin[\\/]vite\.js'))
} | ForEach-Object { Stop-Process -Id $_.ProcessId -ErrorAction SilentlyContinue }
Write-Output 'Project API and web processes stopped. The SQLite data file is retained.'
