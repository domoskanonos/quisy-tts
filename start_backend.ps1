#!/usr/bin/env pwsh
# Minimaler Starter für das Backend — startet uv/uvicorn ohne weitere Logik

$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

# Read .env for BACKEND_PORT and HOST (keeps parity with frontend starter)
$envFile = Join-Path $PSScriptRoot '.env'
if (Test-Path $envFile) {
    foreach ($ln in Get-Content $envFile) {
        $line = $ln.Trim()
        if ($line -eq '' -or $line.StartsWith('#')) { continue }
        $parts = $line -split '=',2
        if ($parts.Count -eq 2) {
            $name = $parts[0].Trim()
            $val  = $parts[1].Trim()
            if ($name -eq 'BACKEND_PORT' -and $val) { $env:PORT = $val }
            if ($name -eq 'HOST' -and $val) { $env:HOST = $val }
        }
    }
}

# Bevorzugt: uv aus .venv (wenn vorhanden)
$venvUv = Join-Path $PSScriptRoot '.venv\Scripts\uv.exe'
if (Test-Path $venvUv) {
    $hostArg = $env:HOST -or '127.0.0.1'
    $portArg = $env:PORT -or '8080'
    Write-Host "Starte: $venvUv run src/main.py --host $hostArg --port $portArg" -ForegroundColor Cyan
    Start-Process powershell -ArgumentList '-NoExit', '-Command', "& '$venvUv' run src/main.py --host $hostArg --port $portArg"
    return
}

# Fallback: python aus .venv (falls vorhanden) -> python -m uvicorn
$venvPy = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (Test-Path $venvPy) {
    $hostArg = $env:HOST -or '127.0.0.1'
    $portArg = $env:PORT -or '8080'
    Write-Host "Starte: $venvPy -m uvicorn main:app --app-dir src --host $hostArg --port $portArg" -ForegroundColor Cyan
    Start-Process powershell -ArgumentList '-NoExit', '-Command', "& '$venvPy' -m uvicorn main:app --app-dir src --host $hostArg --port $portArg"
    return
}

# Letzter Fallback: versuche 'uv' vom PATH
$hostArg = $env:HOST -or '127.0.0.1'
$portArg = $env:PORT -or '8080'
Write-Host "Starte: uv run src/main.py --host $hostArg --port $portArg (system UV)" -ForegroundColor Cyan
Start-Process powershell -ArgumentList '-NoExit', '-Command', "uv run src/main.py --host $hostArg --port $portArg"
