# Deploy Backend no Fly.io (Gratuito)

## 🎯 Por Que Fly.io?

- ✅ **Totalmente gratuito** (tier generoso, sem cartão necessário inicialmente)
- ✅ **Suporta OCR** via Docker (Tesseract instalado)
- ✅ **Performance excelente** (data center em São Paulo)
- ✅ **HTTPS automático**
- ✅ **Auto-scale** (desliga quando não está em uso)

---

## 📋 Pré-requisitos

1. Conta no Fly.io: https://fly.io/app/sign-up
2. Fly CLI instalado no Windows

---

## 🚀 Passo a Passo

### 1️⃣ Instalar Fly CLI

No PowerShell (como Administrador):

```powershell
iwr https://fly.io/install.ps1 -useb | iex
```

**OU** via winget:

```powershell
winget install Fly.io.fly
```

Depois, **feche e reabra o terminal** para atualizar o PATH.

### 2️⃣ Login no Fly.io

```powershell
flyctl auth login
```

Isso abre o navegador para você fazer login.

### 3️⃣ Criar Aplicação

No diretório do projeto:

```powershell
cd d:\Snap
flyctl launch --no-deploy
```

**Perguntas que aparecerão:**

- `Choose an app name:` → **docsplit** (ou deixe em branco para gerar)
- `Choose a region:` → **gru (São Paulo, Brazil)**
- `Would you like to set up a PostgreSQL database?` → **No**
- `Would you like to set up an Upstash Redis database?` → **No**

### 4️⃣ Configurar Secrets (Variáveis de Ambiente)

```powershell
# Supabase
flyctl secrets set SUPABASE_URL="https://pjryxiwzpfbypawxgios.supabase.co"
flyctl secrets set SUPABASE_ANON_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBqcnl4aXd6cGZieXBhd3hnaW9zIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODcwNzM2NzIsImV4cCI6MjEwMjY0OTY3Mn0.d3kIGnBFJxMPIEDVY6VhZcEr0-3Gwek4KLn5W2Tc8bQ"
flyctl secrets set SUPABASE_SERVICE_ROLE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBqcnl4aXd6cGZieXBhd3hnaW9zIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NzA3MzY3MiwiZXhwIjoyMTAyNjQ5NjcyfQ.idRemW5wRlkXqcRDBoJCHDCr4vyxL15pxi3bs2aqL9k"

# Mercado Pago (TESTE)
flyctl secrets set MERCADOPAGO_ACCESS_TOKEN="TEST-2185639579586130-081815-48207165dc6d03582a3e0389311d03b6-3219911998"
flyctl secrets set MERCADOPAGO_PUBLIC_KEY="TEST-3122cb01-0316-4dc4-a303-af31df838799"

# Frontend
flyctl secrets set FRONTEND_URL="https://doc-split-beta.vercel.app"

# OpenRouter (Opcional)
flyctl secrets set OPENROUTER_API_KEY="sua-chave-aqui"
flyctl secrets set OPENROUTER_MODEL="openai/gpt-4o-mini"
```

### 5️⃣ Deploy

```powershell
flyctl deploy
```

Aguarde 5-10 minutos (primeira vez demora mais).

### 6️⃣ Verificar Deploy

```powershell
flyctl status
flyctl open
```

Ou acesse: **https://docsplit.fly.dev/health**

Deve retornar:

```json
{
  "status": "ok",
  "version": "0.5.0",
  "ocr_available": true,
  "supabase_connected": true,
  "payments_enabled": true
}
```

---

## 🔄 Atualizações Futuras

Após fazer mudanças no código:

```powershell
git add .
git commit -m "feat: sua mudança"
git push origin main
flyctl deploy
```

---

## 📊 Monitoramento

### Ver Logs em Tempo Real

```powershell
flyctl logs
```

### Abrir Dashboard

```powershell
flyctl dashboard
```

Ou acesse: https://fly.io/dashboard

### Ver Status

```powershell
flyctl status
```

---

## ⚙️ Configurações Importantes

### Escalar (se necessário)

```powershell
# Aumentar memória
flyctl scale memory 2048

# Aumentar CPU
flyctl scale vm shared-cpu-2x

# Ver escala atual
flyctl scale show
```

### Região (São Paulo)

```powershell
flyctl regions list
flyctl regions set gru
```

---

## 💰 Custos (Gratuito)

O **tier gratuito** do Fly.io inclui:

- **3 VMs compartilhadas** (256MB RAM cada)
- **3GB de armazenamento**
- **160GB de transferência/mês**

**Suficiente para testes e uso moderado!**

Se ultrapassar, você receberá email avisando.

---

## 🐛 Troubleshooting

### Erro: "Could not resolve host"

```powershell
flyctl doctor
```

### Erro: "Health check failed"

Verifique se o endpoint `/health` está respondendo:

```powershell
flyctl logs
```

### Build Lento

É normal na primeira vez (10-15 minutos). Próximos builds: 2-3 minutos.

### App Desligada (Auto-scale)

O Fly.io desliga a VM quando não está em uso (economiza recursos). Ela liga automaticamente quando recebe uma requisição (demora 2-3 segundos).

---

## 🔗 Links Úteis

- Dashboard: https://fly.io/dashboard
- Documentação: https://fly.io/docs/
- Status: https://status.flyio.net/
- Suporte: https://community.fly.io/

---

## ✅ Próximos Passos

Depois do deploy:

1. ✅ Copiar URL do Fly.io (ex: `https://docsplit.fly.dev`)
2. ⏳ Atualizar `VITE_BACKEND_URL` no Vercel
3. ⏳ Redeploy do frontend
4. ⏳ Deploy do webhook (Supabase Edge Function)
5. ⏳ Configurar webhook no Mercado Pago
6. ✅ **Sistema 100% funcionando!**

---

**Comando Único para Copiar e Colar (após login):**

```powershell
cd d:\Snap
flyctl launch --no-deploy --name docsplit --region gru
flyctl secrets set SUPABASE_URL="https://pjryxiwzpfbypawxgios.supabase.co" SUPABASE_ANON_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBqcnl4aXd6cGZieXBhd3hnaW9zIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODcwNzM2NzIsImV4cCI6MjEwMjY0OTY3Mn0.d3kIGnBFJxMPIEDVY6VhZcEr0-3Gwek4KLn5W2Tc8bQ" SUPABASE_SERVICE_ROLE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBqcnl4aXd6cGZieXBhd3hnaW9zIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NzA3MzY3MiwiZXhwIjoyMTAyNjQ5NjcyfQ.idRemW5wRlkXqcRDBoJCHDCr4vyxL15pxi3bs2aqL9k" MERCADOPAGO_ACCESS_TOKEN="TEST-2185639579586130-081815-48207165dc6d03582a3e0389311d03b6-3219911998" MERCADOPAGO_PUBLIC_KEY="TEST-3122cb01-0316-4dc4-a303-af31df838799" FRONTEND_URL="https://doc-split-beta.vercel.app"
flyctl deploy
```
