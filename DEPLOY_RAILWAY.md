# Deploy Backend no Railway

## 📋 O Que o Railway Oferece

- ✅ Suporte completo a Python com OCR (Tesseract)
- ✅ Poppler-utils para manipulação de PDF
- ✅ 500 horas grátis/mês ($5 em créditos)
- ✅ Auto-deploy a cada git push
- ✅ Domínio HTTPS automático
- ✅ Logs em tempo real

---

## 🚀 Passo a Passo

### 1️⃣ Criar Conta no Railway

1. Acesse: https://railway.app/
2. Clique em **"Start a New Project"**
3. Faça login com sua conta GitHub

### 2️⃣ Criar Novo Projeto

1. Clique em **"New Project"**
2. Selecione **"Deploy from GitHub repo"**
3. Escolha o repositório **DocSplit**
4. Railway detectará automaticamente o `nixpacks.toml` e `Procfile`

### 3️⃣ Configurar Variáveis de Ambiente

Na página do projeto, clique em **"Variables"** e adicione:

```bash
# Supabase
SUPABASE_URL=https://pjryxiwzpfbypawxgios.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBqcnl4aXd6cGZieXBhd3hnaW9zIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODcwNzM2NzIsImV4cCI6MjEwMjY0OTY3Mn0.d3kIGnBFJxMPIEDVY6VhZcEr0-3Gwek4KLn5W2Tc8bQ
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBqcnl4aXd6cGZieXBhd3hnaW9zIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NzA3MzY3MiwiZXhwIjoyMTAyNjQ5NjcyfQ.idRemW5wRlkXqcRDBoJCHDCr4vyxL15pxi3bs2aqL9k

# Mercado Pago (TESTE)
MERCADOPAGO_ACCESS_TOKEN=TEST-2185639579586130-081815-48207165dc6d03582a3e0389311d03b6-3219911998
MERCADOPAGO_PUBLIC_KEY=TEST-3122cb01-0316-4dc4-a303-af31df838799

# OpenRouter (Classificação LLM - Opcional)
OPENROUTER_API_KEY=sua-chave-aqui
OPENROUTER_MODEL=openai/gpt-4o-mini

# Frontend URL
FRONTEND_URL=https://doc-split-beta.vercel.app

# Ambiente
ENVIRONMENT=production

# OCR Settings
OCR_DPI=180
OCR_LANGUAGE=por
CLASSIFICATION_CONFIDENCE_THRESHOLD=0.8
```

### 4️⃣ Configurar Build

Railway deve detectar automaticamente o `nixpacks.toml`, mas se necessário:

1. Clique em **"Settings"**
2. Em **"Build"**, verifique:
   - **Build Command:** (deixe vazio, usa nixpacks.toml)
   - **Start Command:** `uvicorn api.index:app --host 0.0.0.0 --port $PORT`

### 5️⃣ Deploy

1. Clique em **"Deploy"**
2. Aguarde o build (5-10 minutos primeira vez)
3. Copie a URL gerada (exemplo: `https://docsplit-production.up.railway.app`)

### 6️⃣ Testar o Backend

Acesse: `https://seu-app.up.railway.app/health`

Deve retornar:

```json
{
  "status": "ok",
  "version": "0.5.0",
  "environment": "production",
  "ocr_available": true,
  "llm_available": true,
  "supabase_connected": true,
  "payments_enabled": true
}
```

---

## 🔄 Atualizar Frontend com URL do Backend

Depois de obter a URL do Railway:

1. Acesse: https://vercel.com/sbarros82/doc-split/settings/environment-variables
2. Edite `VITE_BACKEND_URL`
3. Mude de `http://localhost:8000` para `https://seu-app.up.railway.app`
4. Clique em **"Save"**
5. Vá em **"Deployments"** e clique em **"Redeploy"**

---

## 📊 Monitoramento

### Logs

```
railway logs
```

Ou acesse o painel: https://railway.app/project/seu-projeto

### Métricas

- CPU, memória, rede disponíveis no dashboard
- Alertas de erro automáticos

---

## 💰 Custos

- **Grátis:** $5/mês em créditos (500 horas de execução)
- **Hobby:** $5/mês (mais horas se necessário)
- **Pro:** $20/mês (uso ilimitado)

---

## 🐛 Troubleshooting

### Erro: "Tesseract not found"

Verifique se o `nixpacks.toml` inclui `tesseract-ocr` e `tesseract-ocr-por`.

### Erro: "Module not found"

Verifique se todos os módulos estão no `requirements.txt`.

### Deploy Lento

Primeira vez demora 5-10 minutos. Próximos deploys: 2-3 minutos.

---

## 📝 Próximos Passos

1. ✅ Deploy do backend no Railway
2. ⏳ Atualizar `VITE_BACKEND_URL` no Vercel
3. ⏳ Deploy do webhook no Supabase
4. ⏳ Configurar webhook no Mercado Pago
5. ⏳ Testar pagamento end-to-end

---

## 🔗 Links Úteis

- Railway Dashboard: https://railway.app/dashboard
- Documentação: https://docs.railway.app/
- Status Page: https://railway.statuspage.io/
