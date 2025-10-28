param(
    [string]$venvPath = ".\venv\Scripts\python.exe"
)

# Папка скрипта
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Папка проекта (одна выше build)
$projectDir = Join-Path $scriptDir ".."

# Переходим в папку проекта
Set-Location -Path $projectDir

# Путь к Python из venv
$venvPython = Join-Path $projectDir "venv\Scripts\python.exe"

# Путь к основному скрипту
$mainScript = Join-Path $projectDir "musical_loto.py"

# Путь к ресурсам
$resources = Join-Path $projectDir "resources;resources"

# Путь к иконке .ico
$iconPath = Join-Path $projectDir "resources\app_icon.ico"

$iconPath = Join-Path $projectDir "resources\icon.ico"

# Запуск PyInstaller
& $venvPython -m PyInstaller `
    --noconfirm `
    --onefile `
    --windowed `
    --icon $iconPath `
    --add-data $resources `
    $mainScript
