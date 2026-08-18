# ✅ Backend Deployado - Próximos Passos

## 🎉 Status Atual

- ✅ Backend online: **https://docsplit.fly.dev**
- ⚠️ Variáveis de ambiente precisam ser reaplicadas
- ⏳ Frontend precisa ser atualizado com nova URL

---

## 🔧 Passo 1: Reconfigurar Secrets no Fly.io

As variáveis foram adicionadas ANTES do primeiro deploy. Precisamos reaplicá-las:

### Opção A: Via Interface Web (Recomendado)

1. Acesse: https://fly.io/dashboard/docsplit
2. Clique em **"Secrets"** no menu lateral
3. Verifique se todas as 6 variáveis estão lá:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `MERCADOPAGO_ACCESS_TOKEN`
   - `MERCADOPAGO_PUBLIC_KEY`
   - `FRONTEND_URL`

4. **Se alguma estiver faltando, adicione novamente:**

```
SUPABASE_URL = https://pjryxiwzpfbypawxgios.supabase.co
SUPABASE_ANON_KEY = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBqcnl4aXd6cGZieXBhd3hnaW9zIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODcwNzM2NzIsImV4cCI6MjEwMjY0OTY3Mn0.d3kIGnBFJxMPIEDVY6VhZcEr0-3Gwek4KLn5W2Tc8bQ
SUPABASE_SERVICE_ROLE_KEY = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBqcnl4aXd6cGZieXBhd3hnaW9zIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NzA3MzY3MiwiZXhwIjoyMTAyNjQ5NjcyfQ.idRemW5wRlkXqcRDBoJCHDCr4vyxL15pxi3bs2aqL9k
MERCADOPAGO_ACCESS_TOKEN = TEST-2185639579586130-081815-48207165dc6d03582a3e0389311d03b6-3219911998
MERCADOPAGO_PUBLIC_KEY = TEST-3122cb01-0316-4dc4-a303-af31df838799
FRONTEND_URL = https://doc-split-beta.vercel.app
```

5. Adicione também:
```
ENVIRONMENT = production
```

6. **Reinicie o app:**
   - Clique em **"Restart"** ou vá em **"Machines"** → **"Restart Machine"**

### Opção B: Via CLI (PowerShell)

```powershell
$env:PATH += ";C:\Users\SergioBarros\.fly\bin"
cd d:\Snap

flyctl secrets set SUPABASE_URL="https://pjryxiwzpfbypawxgios.supabase.co" SUPABASE_ANON_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBqcnl4aXd6cGZieXBhd3hnaW9zIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODcwNzM2NzIsImV4cCI6MjEwMjY0OTY3Mn0.d3kIGnBFJxMPIEDVY6VhZcEr0-3Gwek4KLn5W2Tc8bQ" SUPABASE_SERVICE_ROLE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBqcnl4aXd6cGZieXBhd3hnaW9zIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NzA3MzY3MiwiZXhwIjoyMTAyNjQ5NjcyfQ.idRemW5wRlkXqcRDBoJCHDCr4vyxL15pxi3bs2aqL9k" MERCADOPAGO_ACCESS_TOKEN="TEST-2185639579586130-081815-48207165dc6d03582a3e0389311d03b6-3219911998" MERCADOPAGO_PUBLIC_KEY="TEST-3122cb01-0316-4dc4-a303-af31df838799" FRONTEND_URL="https://doc-split-beta.vercel.app" ENVIRONMENT="production" -a docsplit
```

---

## 🌐 Passo 2: Atualizar Frontend no Vercel

1. Acesse: https://vercel.com/sbarros82/doc-split/settings/environment-variables

2. **Edite** a variável `VITE_BACKEND_URL`:
   - Valor antigo: `http://localhost:8000`
   - **Novo valor:** `https://docsplit.fly.dev`

3. Clique em **"Save"**

4. Vá em **"Deployments"** → Clique em **"Redeploy"** no último deployment

5. Aguarde 2-3 minutos

---

## ✅ Passo 3: Testar Tudo

Depois do redeploy do Vercel, teste:

### Backend (direto):
```
https://docsplit.fly.dev/health
```

Deve retornar:
```json
{
  "status": "ok",
  "supabase_connected": true,
  "payments_enabled": true,
  "environment": "production"
}
```

### Frontend:
```
https://doc-split-beta.vercel.app
```

- Teste fazer login
- Teste a página de preços
- Verifique se o dashboard carrega

---

## 📋 Checklist

- [ ] Verificar secrets no Fly.io (https://fly.io/dashboard/docsplit → Secrets)
- [ ] Adicionar `ENVIRONMENT=production` se não existir
- [ ] Reiniciar app no Fly.io
- [ ] Testar `/health` → verificar `supabase_connected: true`
- [ ] Atualizar `VITE_BACKEND_URL` no Vercel
- [ ] Redeploy frontend no Vercel
- [ ] Testar frontend completo

---

## 🐛 Se algo não funcionar

**Backend não conecta ao Supabase:**
- Verifique se `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` estão corretas nos secrets
- Reinicie o app no Fly.io

**Frontend não conecta ao backend:**
- Verifique se `VITE_BACKEND_URL` está com `https://docsplit.fly.dev` (sem barra no final)
- Faça redeploy do frontend

**Erro 500 no backend:**
- Veja os logs: https://fly.io/dashboard/docsplit → Logs

---

## 🎯 Próximos Passos (Depois de Tudo Funcionando)

1. ⏳ Deploy Edge Function (webhook) no Supabase
2. ⏳ Configurar webhook no Mercado Pago
3. ⏳ Testar pagamento end-to-end
4. ✅ **Sistema 100% funcional!**

---

**Me avise quando terminar os passos 1 e 2, e eu vou testar automaticamente!** 🚀
