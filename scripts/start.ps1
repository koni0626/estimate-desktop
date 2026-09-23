$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $taskRoot
$taskPython = Join-Path $taskRoot '.venv\Scripts\python.exe'
$taskVite = Join-Path $taskRoot 'frontend\node_modules\vite\bin\vite.js'
if (-not (Test-Path -LiteralPath $taskPython) -or -not (Test-Path -LiteralPath $taskVite)) { throw 'Run scripts\setup.ps1 first.' }
if (-not (Test-Path -LiteralPath '.env')) { throw 'DATABASE_URL is missing. Create .env first.' }

function Test-TaskPort([int]$Port) {
    $taskClient = [Net.Sockets.TcpClient]::new()
    try { $taskConnect = $taskClient.ConnectAsync('127.0.0.1', $Port); return ($taskConnect.Wait(300) -and $taskClient.Connected) } catch { return $false } finally { $taskClient.Dispose() }
}

if ((Test-TaskPort 8005) -or (Test-TaskPort 5185)) { throw 'Port 8005 or 5185 is already in use. Stop the existing process before starting this project.' }
New-Item -ItemType Directory -Path 'data' -Force | Out-Null
& $taskPython -m alembic upgrade head
if ($LASTEXITCODE -ne 0) { throw 'Migration failed.' }
Start-Process -FilePath $taskPython -ArgumentList @('-m','uvicorn','backend.app.main:app','--host','127.0.0.1','--port','8005') -WorkingDirectory $taskRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskRoot 'data\api.log') -RedirectStandardError (Join-Path $taskRoot 'data\api-error.log') | Out-Null
$taskApiReady = $false
for ($taskAttempt=0; $taskAttempt -lt 40; $taskAttempt++) {
    try {
        $taskHealth = Invoke-RestMethod -Uri 'http://127.0.0.1:8005/api/health' -TimeoutSec 2
        if ($taskHealth.status -eq 'ok' -and $taskHealth.database -eq 'sqlite') { $taskApiReady = $true; break }
    } catch { }
    Start-Sleep -Milliseconds 250
}
if (-not $taskApiReady) { throw 'API startup failed. Check data\api-error.log.' }
Start-Process -FilePath (Get-Command node).Source -ArgumentList @(('"'+$taskVite+'"'),'--host','127.0.0.1') -WorkingDirectory (Join-Path $taskRoot 'frontend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskRoot 'data\web.log') -RedirectStandardError (Join-Path $taskRoot 'data\web-error.log') | Out-Null
$taskWebReady = $false
for ($taskAttempt=0; $taskAttempt -lt 40; $taskAttempt++) {
    try {
        $taskWebPage = Invoke-WebRequest -Uri 'http://127.0.0.1:5185' -TimeoutSec 2
        if ($taskWebPage.Content -like '*見積管理システム*') { $taskWebReady = $true; break }
    } catch { }
    Start-Sleep -Milliseconds 250
}
if (-not $taskWebReady) { throw 'Web startup failed. Check data\web-error.log.' }
Write-Output 'App: http://127.0.0.1:5185  | API: http://127.0.0.1:8005/docs'
