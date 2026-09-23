param([switch]$Demo)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $taskRoot
if (-not (Test-Path -LiteralPath '.env')) {
    Copy-Item -LiteralPath '.env.example' -Destination '.env'
}
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) { py -3.14 -m venv .venv }
& '.\.venv\Scripts\python.exe' -m pip install -r requirements.lock.txt
if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }
Push-Location -LiteralPath 'frontend'
try {
    npm ci
    if ($LASTEXITCODE -ne 0) { throw 'Frontend installation failed.' }
} finally { Pop-Location }
New-Item -ItemType Directory -Path 'data' -Force | Out-Null
& '.\.venv\Scripts\python.exe' -m alembic upgrade head
if ($LASTEXITCODE -ne 0) { throw 'Migration failed.' }
& '.\.venv\Scripts\python.exe' scripts\prepare_font.py
if ($LASTEXITCODE -ne 0) { throw 'Font preparation failed.' }
if ($Demo) {
    & '.\.venv\Scripts\python.exe' -m backend.seed
    if ($LASTEXITCODE -ne 0) { throw 'Demo seed failed.' }
}
Write-Output 'Setup complete. Start with .\scripts\start.ps1'
