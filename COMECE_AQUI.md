# 🚀 Comece Aqui — Próximos Passos

**Você autorizou desenvolver 1, 2 e 3:**
1. ✅ Backend completo (Supabase + créditos + Mercado Pago)
2. ✅ Frontend monetizado (login, dashboard, checkout)
3. ✅ Landing page SEO (converter visitantes)

**Tudo foi implementado!** Agora siga esta ordem:

---

## 📋 Checklist Rápido (2-3 horas)

### Passo 1: Supabase (15 min)

- [ ] Criar conta: [https://supabase.com](https://supabase.com)
- [ ] **New Project** → Nome: `docsplit-prod`
- [ ] **SQL Editor** → Cole `d:\Snap\supabase\schema.sql` → **Run**
- [ ] **Settings → API** → Copie:
  - Project URL
  - anon public key
  - service_role key
- [ ] Cole no `.env` (use `.env.example` como template)

**✅ Pronto!** Banco criado com todas as tabelas.

---

### Passo 2: Mercado Pago (10 min)

- [ ] Criar conta empresa: [https://www.mercadopago.com.br](https://www.mercadopago.com.br)
- [ ] **Developers → Suas aplicações → Criar aplicação**
- [ ] Nome: **DocSplit**, Produto: **Checkout Pro**
- [ ] **Credenciais de teste** (sandbox):
  - Access Token: `TEST-...`
  - Public Key: `TEST-...`
- [ ] Cole no `.env`

**✅ Pronto!** Pode testar pagamentos sem cobrar de verdade.

---

### Passo 3: Deploy Webhook (15 min)

```powershell
# Instalar CLI
npm install -g supabase

# Login
supabase login

# Linkar projeto (copie Project Ref da URL do Supabase)
cd d:\Snap
supabase link --project-ref SEU_PROJECT_REF

# Deploy função
supabase functions deploy handle-mercadopago-webhook

# Configurar secrets
supabase secrets set MERCADOPAGO_ACCESS_TOKEN=TEST-...
supabase secrets set SUPABASE_URL=https://xxx.supabase.co
supabase secrets set SUPABASE_SERVICE_ROLE_KEY=eyJ...
```

**✅ Pronto!** Webhook rodando em Edge Function.

---

### Passo 4: Configurar Webhook no Mercado Pago (5 min)

- [ ] Painel MP → **Suas aplicações** → Sua app → **Webhooks**
- [ ] **Nova URL de notificação**
- [ ] Cole: `https://xxx.supabase.co/functions/v1/handle-mercadopago-webhook`
- [ ] Eventos: **Pagamentos**
- [ ] **Salvar**

**✅ Pronto!** Mercado Pago notifica quando alguém paga.

---

### Passo 5: Testar Localmente (30 min)

#### Backend

```powershell
cd d:\Snap
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn api.index:app --reload --host 0.0.0.0 --port 8000
```

Abra: `http://localhost:8000/api/health`

Deve retornar:
```json
{
  "status": "ok",
  "supabase_connected": true,
  "payments_enabled": true
}
```

#### Frontend

```powershell
cd d:\Snap\frontend
npm install

# Criar .env.local
echo "VITE_SUPABASE_URL=https://xxx.supabase.co" > .env.local
echo "VITE_SUPABASE_ANON_KEY=eyJ..." >> .env.local
echo "VITE_BACKEND_URL=http://localhost:8000" >> .env.local
echo "VITE_MERCADOPAGO_PUBLIC_KEY=TEST-..." >> .env.local

npm run dev
```

Abra: `http://localhost:5173`

**✅ Pronto!** Sistema rodando local.

---

### Passo 6: Teste Completo (15 min)

1. **Cadastro**
   - Clique **Criar conta**
   - Use email + senha
   - Confirme email na caixa de entrada

2. **Verificar usuário criado**
   - Supabase → **Table Editor** → **users**
   - Deve aparecer sua linha

3. **Comprar créditos (sandbox)**
   - Clique **Adicionar créditos** → **R$ 5**
   - Checkout abre
   - Cartão de teste:
     ```
     5031 4332 1540 6351
     CVV: 123
     Validade: 11/25
     Nome: APRO
     ```
   - Confirme

4. **Verificar webhook**
   - Supabase → **Edge Functions** → **Logs**
   - Deve aparecer: `✅ 50 MB adicionados`

5. **Verificar créditos**
   - Dashboard deve mostrar **50 MB disponíveis**

6. **Upload PDF**
   - Arraste um PDF pequeno
   - Sistema processa e desconta créditos
   - Baixe ZIP

**✅ Tudo funcionando!** Agora pode fazer deploy.

---

## 🌐 Deploy Produção (1 hora)

### Backend → Railway

1. [https://railway.app](https://railway.app)
2. **Deploy from GitHub**
3. **Variables** → adicione todas do `.env`
4. **Generate Domain** → `https://docsplit-api.railway.app`

### Frontend → Vercel

```powershell
npm install -g vercel
vercel login
cd d:\Snap\frontend
vercel --prod
```

Adicione variáveis:
- `VITE_BACKEND_URL` = `https://docsplit-api.railway.app`
- `VITE_SUPABASE_URL` = ...
- `VITE_SUPABASE_ANON_KEY` = ...
- `VITE_MERCADOPAGO_PUBLIC_KEY` = ...

**✅ No ar!** URL: `https://docsplit.vercel.app`

---

## 🎯 Próximos Passos (Marketing)

### Semana 1

- [ ] Trocar credenciais de **teste** para **produção** (Mercado Pago)
- [ ] Cadastrar no Google Search Console
- [ ] Google Analytics
- [ ] Testar fluxo completo com cartão real (seu próprio)

### Semana 2

- [ ] Criar 3 artigos SEO:
  - "Como separar boletos de um PDF"
  - "Organizar documentos fiscais automaticamente"
  - "Dividir PDF com múltiplas notas fiscais"
- [ ] Publicar no LinkedIn/Facebook
- [ ] Enviar para amigos contadores

### Semana 3

- [ ] Google Ads (R$ 100/mês teste)
- [ ] Anúncios Facebook (R$ 50/mês)
- [ ] Email marketing (Mailchimp grátis até 500 contatos)

### Mês 2

- [ ] Programa de afiliados (20% comissão)
- [ ] Integrações (Zapier, Make)
- [ ] Assinatura mensal (R$ 19/mês)

---

## 📞 Ajuda

Se travar em algum passo:

1. **SETUP_SUPABASE.md** — guia detalhado Supabase
2. **DEPLOY_COMPLETO.md** — checklist passo a passo
3. **RESUMO_IMPLEMENTACAO.md** — arquivos criados e estrutura

**Documentos criados:**
- `PLANO_MONETIZACAO.md` — estratégia completa
- `SETUP_SUPABASE.md` — setup banco e auth
- `DEPLOY_COMPLETO.md` — deploy produção
- `RESUMO_IMPLEMENTACAO.md` — o que foi feito
- `COMECE_AQUI.md` — este arquivo

---

## ✅ Status

**✅ Backend completo**
- FastAPI + Supabase + Mercado Pago
- Sistema de créditos
- Webhook automático

**✅ Frontend completo**
- React + TypeScript + Tailwind
- Login/cadastro (email + Google)
- Dashboard usuário
- Landing page SEO
- Checkout Mercado Pago

**✅ Documentação completa**
- 6 guias detalhados
- Schema SQL
- Edge Function

**🚀 Pronto para lançar!**

Só falta:
1. Setup Supabase (15 min)
2. Setup Mercado Pago (10 min)
3. Deploy (1 hora)

**Bora?** 💪
