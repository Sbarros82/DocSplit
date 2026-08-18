# Sobe a API + frontend na máquina e na rede local (porta 8000)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".\venv\Scripts\python.exe")) {
    Write-Host "Criando ambiente virtual..."
    python -m venv venv
}

& .\venv\Scripts\python.exe -m pip install -q -r requirements-local.txt
Write-Host "Neste PC: http://127.0.0.1:8000"
Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -notlike "127.*" -and $_.PrefixOrigin -ne "WellKnown" } |
    ForEach-Object { Write-Host ("Na rede:  http://{0}:8000" -f $_.IPAddress) }
& .\venv\Scripts\python.exe -m uvicorn api.index:app --reload --host 0.0.0.0 --port 8000
