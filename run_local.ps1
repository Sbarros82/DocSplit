# Sobe a API + frontend em http://127.0.0.1:8000
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".\venv\Scripts\python.exe")) {
    Write-Host "Criando ambiente virtual..."
    python -m venv venv
}

& .\venv\Scripts\python.exe -m pip install -q -r requirements-local.txt
Write-Host "DocSplit em http://127.0.0.1:8000"
& .\venv\Scripts\python.exe -m uvicorn api.index:app --reload --host 127.0.0.1 --port 8000
