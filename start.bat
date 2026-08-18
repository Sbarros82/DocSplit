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
echo Neste PC:     http://127.0.0.1:8000
echo Na mesma rede (celular/outro computador):
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i /c:"IPv4"') do (
  for /f "tokens=1" %%b in ("%%a") do echo   http://%%b:8000
)
echo.
echo Se o outro aparelho nao abrir: permita Python no Firewall do Windows
echo ^(rede privada^). Para encerrar, feche esta janela ou Ctrl+C.
echo.

start "" "http://127.0.0.1:8000"
"venv\Scripts\python.exe" -m uvicorn api.index:app --reload --host 0.0.0.0 --port 8000
pause
