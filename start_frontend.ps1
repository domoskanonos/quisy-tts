#!/usr/bin/env pwsh
#!/usr/bin/env pwsh
# start_frontend.ps1 - liest BACKEND_PORT aus .env und startet Angular mit einer temporären Proxy-Config

$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

# Default backend port
$backendPort = '8080'
$envFile = Join-Path $PSScriptRoot '.env'
if (Test-Path $envFile) {
    foreach ($ln in Get-Content $envFile) {
        $line = $ln.Trim()
        if ($line -eq '' -or $line.StartsWith('#')) { continue }
        $parts = $line -split '=',2
        if ($parts.Count -eq 2) {
            $name = $parts[0].Trim()
            $val  = $parts[1].Trim()
            if ($name -eq 'BACKEND_PORT' -and $val) { $backendPort = $val; break }
        }
    }
}

# Erzeuge temporäre Proxy-Config im frontend-Ordner
$proxyObj = @{
    "/api" = @{
        target = "http://127.0.0.1:$backendPort"
        secure = $false
        changeOrigin = $true
    }
}
$proxyJson = $proxyObj | ConvertTo-Json -Depth 10

$proxyPath = Join-Path $PSScriptRoot 'frontend\proxy.local.temp.json'
# Schreibe JSON ohne BOM
$proxyJson = $proxyJson.TrimStart([char]0xFEFF)
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllBytes($proxyPath, $utf8NoBom.GetBytes($proxyJson))

# Wähle Frontend-Port (versuche 4200, wenn belegt versuche zu beenden oder wähle 4201..4210)
$frontendPort = 4200
try {
    $listen = Get-NetTCPConnection -LocalPort $frontendPort -ErrorAction SilentlyContinue | Where-Object { $_.State -eq 'Listen' }
} catch { $listen = $null }
if ($listen) {
    $ownerPid = $listen.OwningProcess
    try { $owner = Get-CimInstance Win32_Process -Filter "ProcessId = $ownerPid" -ErrorAction SilentlyContinue } catch { $owner = $null }
    $isDev = $false
    if ($owner) {
        $cmd = $owner.CommandLine
        $exe = $owner.ExecutablePath
        if ((($cmd -ne $null) -and ($cmd -match 'ng|node|npm')) -or (($exe -ne $null) -and ($exe -match 'node'))) { $isDev = $true }
    }
    if ($isDev) {
        Write-Host "Port $frontendPort wird von Prozess $ownerPid belegt. Versuche zu beenden..." -ForegroundColor Yellow
        try { Stop-Process -Id $ownerPid -Force -ErrorAction SilentlyContinue; Start-Sleep -Milliseconds 500 } catch { }
        try { $listen = Get-NetTCPConnection -LocalPort $frontendPort -ErrorAction SilentlyContinue | Where-Object { $_.State -eq 'Listen' } } catch { $listen = $null }
        if ($listen) { $frontendPort = $null }
    } else {
        Write-Host "Port $frontendPort ist in Benutzung, wähle alternativen Port..." -ForegroundColor Yellow
        $frontendPort = $null
    }
}
if (-not $frontendPort) {
    for ($p=4200; $p -le 4210; $p++) {
        try { $c = Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue | Where-Object { $_.State -eq 'Listen' } } catch { $c = $null }
        if (-not $c) { $frontendPort = $p; break }
    }
}
if (-not $frontendPort) { Write-Host "Kein freier Frontend-Port gefunden (4200-4210)." -ForegroundColor Red; return }

Write-Host "Starting frontend on http://localhost:$frontendPort with proxy -> http://127.0.0.1:$backendPort" -ForegroundColor Cyan
Start-Process powershell -ArgumentList '-NoExit', '-Command', "cd '$PSScriptRoot\frontend'; npm run start -- --proxy-config '$proxyPath' --port $frontendPort"
