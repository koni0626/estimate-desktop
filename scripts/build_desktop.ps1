$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $taskRoot
$taskPython = Join-Path $taskRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) { throw 'Run scripts\setup.ps1 first.' }
if (-not (Test-Path -LiteralPath 'backend\assets\NotoSansJP.ttf')) { throw 'Run scripts\setup.ps1 to prepare the Japanese font.' }

& $taskPython scripts\make_icon.py
if ($LASTEXITCODE -ne 0) { throw 'Desktop icon generation failed.' }

& $taskPython -m pip install -r requirements-desktop.txt
if ($LASTEXITCODE -ne 0) { throw 'Desktop dependency installation failed.' }

Push-Location -LiteralPath 'frontend'
try {
    npm run build
    if ($LASTEXITCODE -ne 0) { throw 'React build failed.' }
} finally { Pop-Location }

$taskDist = Join-Path $taskRoot 'deliverables\desktop'
$taskWork = Join-Path $taskRoot 'data\pyinstaller-build'
$taskSpec = Join-Path $taskRoot 'data\pyinstaller-spec'
$taskAlembicData = "$(Join-Path $taskRoot 'alembic.ini');."
$taskMigrationsData = "$(Join-Path $taskRoot 'backend\migrations');backend\migrations"
$taskAssetsData = "$(Join-Path $taskRoot 'backend\assets');backend\assets"
$taskFrontendData = "$(Join-Path $taskRoot 'frontend\dist');frontend\dist"
$taskManualData = "$(Join-Path $taskRoot 'docs\manual\ja');docs\manual\ja"
$taskIcon = Join-Path $taskRoot 'desktop-assets\Estimate2.ico'
$taskIconData = "$taskIcon;desktop-assets"
& $taskPython -m PyInstaller --noconfirm --clean --onedir --windowed `
    --name Estimate2 `
    --icon $taskIcon `
    --distpath $taskDist --workpath $taskWork --specpath $taskSpec `
    --add-data $taskAlembicData `
    --add-data $taskMigrationsData `
    --add-data $taskAssetsData `
    --add-data $taskFrontendData `
    --add-data $taskManualData `
    --add-data $taskIconData `
    desktop.py
if ($LASTEXITCODE -ne 0) { throw 'Desktop executable build failed.' }

$taskExe = Join-Path $taskDist 'Estimate2\Estimate2.exe'
if (-not (Test-Path -LiteralPath $taskExe)) { throw 'Estimate2.exe was not created.' }
Copy-Item -LiteralPath (Join-Path $taskRoot 'docs\desktop.md') -Destination (Join-Path $taskDist 'Estimate2\README-ja.md') -Force
& $taskPython scripts\package_desktop.py
if ($LASTEXITCODE -ne 0) { throw 'Desktop ZIP packaging failed.' }
Write-Output "Desktop app: $taskExe"
