#!/usr/bin/env pwsh
# Minimaler Starter für das Backend — startet uv/uvicorn ohne weitere Logik

$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

# Bevorzugt: uv aus .venv (wenn vorhanden)
$venvUv = Join-Path $PSScriptRoot '.venv\Scripts\uv.exe'
if (Test-Path $venvUv) {
    Write-Host "Starte: $venvUv run src/main.py --host 127.0.0.1 --port 8080" -ForegroundColor Cyan
    Start-Process powershell -ArgumentList '-NoExit', '-Command', "& '$venvUv' run src/main.py --host 127.0.0.1 --port 8080"
    return
}

# Fallback: python aus .venv (falls vorhanden) -> python -m uvicorn
$venvPy = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (Test-Path $venvPy) {
    Write-Host "Starte: $venvPy -m uvicorn main:app --app-dir src --host 127.0.0.1 --port 8080" -ForegroundColor Cyan
    Start-Process powershell -ArgumentList '-NoExit', '-Command', "& '$venvPy' -m uvicorn main:app --app-dir src --host 127.0.0.1 --port 8080"
    return
}

# Letzter Fallback: versuche 'uv' vom PATH
Write-Host "Starte: uv run src/main.py --host 127.0.0.1 --port 8080 (system UV)" -ForegroundColor Cyan
Start-Process powershell -ArgumentList '-NoExit', '-Command', "uv run src/main.py --host 127.0.0.1 --port 8080"
