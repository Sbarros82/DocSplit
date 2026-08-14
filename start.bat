@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo   DocSplit — iniciando localmente
echo ========================================
echo.

where python >nul 2>&1
if errorlevel 1 (
  echo Python nao encontrado. Instale Python 3.12+ e marque "Add to PATH".
  pause
  exit /b 1
)

if not exist "venv\Scripts\python.exe" (
  echo Criando ambiente virtual...
  python -m venv venv
  if errorlevel 1 (
    echo Falha ao criar o venv.
    pause
    exit /b 1
  )
)

echo Instalando / atualizando dependencias...
"venv\Scripts\python.exe" -m pip install -q -r requirements-local.txt
if errorlevel 1 (
  echo Falha ao instalar dependencias.
  pause
  exit /b 1
)

if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo.
  echo Arquivo .env criado. Abra-o e cole sua OPENROUTER_API_KEY.
  echo.
)

echo.
echo Abrindo http://127.0.0.1:8000
echo Para encerrar, feche esta janela ou pressione Ctrl+C
echo.

start "" "http://127.0.0.1:8000"
"venv\Scripts\python.exe" -m uvicorn api.index:app --reload --host 127.0.0.1 --port 8000
pause
