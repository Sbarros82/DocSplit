# 🚀 Deploy Backend AGORA (Fly.io - Gratuito)

## ⚡ Quick Start (10 minutos)

### 1️⃣ Instalar Fly CLI

**PowerShell (como Administrador):**

```powershell
iwr https://fly.io/install.ps1 -useb | iex
```

**Depois, feche e reabra o terminal.**

---

### 2️⃣ Login

```powershell
flyctl auth login
```

(Abre o navegador para login)

---

### 3️⃣ Criar App

```powershell
cd d:\Snap
flyctl launch --no-deploy --name docsplit --region gru
```

**Responda "No" para todas as perguntas** (PostgreSQL, Redis, etc.)

---

### 4️⃣ Configurar Secrets (COPIE E COLE TUDO)

```powershell
flyctl secrets set SUPABASE_URL="https://pjryxiwzpfbypawxgios.supabase.co" SUPABASE_ANON_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBqcnl4aXd6cGZieXBhd3hnaW9zIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODcwNzM2NzIsImV4cCI6MjEwMjY0OTY3Mn0.d3kIGnBFJxMPIEDVY6VhZcEr0-3Gwek4KLn5W2Tc8bQ" SUPABASE_SERVICE_ROLE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBqcnl4aXd6cGZieXBhd3hnaW9zIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NzA3MzY3MiwiZXhwIjoyMTAyNjQ5NjcyfQ.idRemW5wRlkXqcRDBoJCHDCr4vyxL15pxi3bs2aqL9k" MERCADOPAGO_ACCESS_TOKEN="TEST-2185639579586130-081815-48207165dc6d03582a3e0389311d03b6-3219911998" MERCADOPAGO_PUBLIC_KEY="TEST-3122cb01-0316-4dc4-a303-af31df838799" FRONTEND_URL="https://doc-split-beta.vercel.app"
```

---

### 5️⃣ Deploy

```powershell
flyctl deploy
```

**Aguarde 5-10 minutos...**

---

### 6️⃣ Testar

```powershell
flyctl open
```

Ou acesse: **https://docsplit.fly.dev/health**

---

## ✅ Depois do Deploy

1. **Copie a URL:** `https://docsplit.fly.dev`
2. **Vá no Vercel:** https://vercel.com/sbarros82/doc-split/settings/environment-variables
3. **Edite** `VITE_BACKEND_URL` e cole `https://docsplit.fly.dev`
4. **Redeploy** o frontend

---

## 🎉 Pronto!

Seu sistema estará 100% online:

- ✅ Frontend: https://doc-split-beta.vercel.app
- ✅ Backend: https://docsplit.fly.dev
- ✅ Banco: Supabase
- ✅ Pagamentos: Mercado Pago (TESTE)

---

## 📊 Comandos Úteis

```powershell
# Ver logs em tempo real
flyctl logs

# Ver status
flyctl status

# Abrir dashboard
flyctl dashboard

# Abrir app no navegador
flyctl open
```

---

## 💰 Custos

**GRATUITO** para uso moderado (até 3 VMs, 160GB transferência/mês).

---

**🚨 Se der erro, me avise e eu resolvo!**
