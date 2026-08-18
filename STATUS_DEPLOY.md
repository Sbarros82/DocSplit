# Status do Deploy - DocSplit

## ✅ COMPLETO

### 1. Supabase (Banco de Dados + Auth)
- [x] Projeto criado: `pjryxiwzpfbypawxgios`
- [x] Schema executado (tables, RLS, functions)
- [x] Credenciais configuradas no `.env`
- [x] URL: https://pjryxiwzpfbypawxgios.supabase.co

### 2. Mercado Pago (Pagamentos)
- [x] MCP configurado e autenticado
- [x] Aplicação criada via MCP: **DocSplit-ceef7** (ID: 2185639579586130)
- [x] Credenciais de TESTE obtidas automaticamente
- [x] Access Token: `TEST-2185639579586130-...`
- [x] Public Key: `TEST-3122cb01-0316-...`
- [x] Dashboard: https://www.mercadopago.com.br/developers/panel/app/2185639579586130

### 3. Frontend (Vercel)
- [x] Deploy completo: **https://doc-split-beta.vercel.app**
- [x] React + Vite + TypeScript + Tailwind
- [x] Landing page com SEO
- [x] Página de preços
- [x] Dashboard de usuário
- [x] Autenticação Supabase configurada

---

## ⏳ PRÓXIMO PASSO: BACKEND (Railway)

### Configuração Pronta
- [x] `Procfile` criado
- [x] `runtime.txt` criado
- [x] `railway.json` criado
- [x] `nixpacks.toml` criado (com Tesseract + Poppler)
- [x] `requirements-railway.txt` criado

### Deploy no Railway

1. **Acesse**: https://railway.app/new
2. **Login** com GitHub
3. **Deploy from GitHub repo** → Selecione **DocSplit**
4. **Configure Variáveis de Ambiente** (copie do `.env`)
5. **Deploy** e aguarde 5-10 minutos
6. **Copie a URL** gerada (ex: `https://docsplit-production.up.railway.app`)

### Depois do Deploy Railway

1. Atualizar `VITE_BACKEND_URL` no Vercel com a URL do Railway
2. Redeploy do frontend no Vercel
3. Testar o endpoint `/health` do backend

---

## ⏳ PENDENTE

### 4. Edge Function (Webhook Mercado Pago)
- [ ] Deploy no Supabase
- [ ] Configurar secrets (SUPABASE_SERVICE_ROLE_KEY)
- [ ] Obter URL do webhook

### 5. Configuração Final Mercado Pago
- [ ] Adicionar URL do webhook no painel
- [ ] Testar pagamento end-to-end

---

## 📊 Resumo Técnico

| Item | Status | URL/Valor |
|------|--------|-----------|
| **Supabase** | ✅ Online | https://pjryxiwzpfbypawxgios.supabase.co |
| **Frontend** | ✅ Online | https://doc-split-beta.vercel.app |
| **Backend** | ⏳ Pendente | Deploy no Railway |
| **Webhook** | ⏳ Pendente | Deploy no Supabase |
| **Mercado Pago** | ✅ Configurado | App ID: 2185639579586130 (TESTE) |

---

## 🎯 Próxima Ação

**Fazer deploy do backend no Railway seguindo o guia:**

📄 Ver arquivo: `DEPLOY_RAILWAY.md`

Depois disso, são só mais 2 passos:
1. Deploy do webhook no Supabase
2. Configurar webhook no Mercado Pago

**E o sistema estará 100% funcional! 🚀**
