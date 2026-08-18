# Script de Deploy para Fly.io
# Execute este arquivo no PowerShell

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  DocSplit - Deploy no Fly.io          " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se flyctl está instalado
if (-not (Get-Command flyctl -ErrorAction SilentlyContinue)) {
    Write-Host "Fly CLI não encontrado. Instalando..." -ForegroundColor Yellow
    iwr https://fly.io/install.ps1 -useb | iex
    $env:PATH += ";$HOME\.fly\bin"
    Write-Host "Fly CLI instalado! Feche e reabra o terminal." -ForegroundColor Green
    exit
}

Write-Host "1. Fazendo login no Fly.io..." -ForegroundColor Yellow
Write-Host "   (Uma página do navegador será aberta)" -ForegroundColor Gray
flyctl auth login

if ($LASTEXITCODE -ne 0) {
    Write-Host "Erro no login. Tente novamente." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "2. Criando aplicação no Fly.io..." -ForegroundColor Yellow
cd d:\Snap
flyctl launch --no-deploy --name docsplit --region gru --copy-config --yes

if ($LASTEXITCODE -ne 0) {
    Write-Host "Erro ao criar app. Pode ser que o nome 'docsplit' já esteja em uso." -ForegroundColor Red
    Write-Host "Tente: flyctl launch --no-deploy --region gru" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "3. Configurando secrets (variáveis de ambiente)..." -ForegroundColor Yellow
flyctl secrets set `
    SUPABASE_URL="https://pjryxiwzpfbypawxgios.supabase.co" `
    SUPABASE_ANON_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBqcnl4aXd6cGZieXBhd3hnaW9zIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODcwNzM2NzIsImV4cCI6MjEwMjY0OTY3Mn0.d3kIGnBFJxMPIEDVY6VhZcEr0-3Gwek4KLn5W2Tc8bQ" `
    SUPABASE_SERVICE_ROLE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBqcnl4aXd6cGZieXBhd3hnaW9zIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NzA3MzY3MiwiZXhwIjoyMTAyNjQ5NjcyfQ.idRemW5wRlkXqcRDBoJCHDCr4vyxL15pxi3bs2aqL9k" `
    MERCADOPAGO_ACCESS_TOKEN="TEST-2185639579586130-081815-48207165dc6d03582a3e0389311d03b6-3219911998" `
    MERCADOPAGO_PUBLIC_KEY="TEST-3122cb01-0316-4dc4-a303-af31df838799" `
    FRONTEND_URL="https://doc-split-beta.vercel.app"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Erro ao configurar secrets." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "4. Fazendo deploy..." -ForegroundColor Yellow
Write-Host "   (Isso vai demorar 5-10 minutos na primeira vez)" -ForegroundColor Gray
flyctl deploy

if ($LASTEXITCODE -ne 0) {
    Write-Host "Erro no deploy." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Deploy concluído com sucesso!        " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Testando o backend..." -ForegroundColor Yellow
flyctl open

Write-Host ""
Write-Host "Próximos passos:" -ForegroundColor Cyan
Write-Host "1. Copie a URL do seu app (ex: https://docsplit.fly.dev)" -ForegroundColor White
Write-Host "2. Vá em: https://vercel.com/sbarros82/doc-split/settings/environment-variables" -ForegroundColor White
Write-Host "3. Edite VITE_BACKEND_URL e cole a URL do Fly.io" -ForegroundColor White
Write-Host "4. Clique em Save e depois Redeploy" -ForegroundColor White
Write-Host ""
