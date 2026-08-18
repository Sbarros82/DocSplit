# 🚀 Deploy Completo — DocSplit Monetizado

**Stack implementada:**
- Frontend React (Vercel)
- Backend FastAPI (Railway)
- Banco Supabase (PostgreSQL grátis)
- Pagamentos Mercado Pago

---

## 📋 Checklist Pré-Deploy

- [ ] Conta Supabase (grátis)
- [ ] Conta Mercado Pago (cadastro empresa)
- [ ] Conta Vercel (frontend)
- [ ] Conta Railway (backend)
- [ ] Node.js instalado
- [ ] Supabase CLI instalado (`npm install -g supabase`)

---

## 1️⃣ Supabase (Banco + Auth)

### Criar Projeto

1. [https://supabase.com/dashboard](https://supabase.com/dashboard)
2. **New Project** → Nome: `docsplit-prod`
3. Senha forte (salve!)
4. Region: **South America (São Paulo)**
5. Aguarde ~2 min

### Executar Schema

1. **SQL Editor** → **New query**
2. Cole `d:\Snap\supabase\schema.sql`
3. **Run** ✅

### Copiar Credenciais

**Settings** → **API**:
- Project URL
- anon public (frontend)
- service_role (backend — NUNCA expor!)

Salve em `.env`:

```bash
# Frontend
VITE_SUPABASE_URL=https://xxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbG...

# Backend
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbG...
```

### Deploy Edge Function (Webhook)

```powershell
cd d:\Snap
supabase login
supabase link --project-ref SEU_PROJECT_REF
supabase functions deploy handle-mercadopago-webhook

# Secrets
supabase secrets set MERCADOPAGO_ACCESS_TOKEN=APP_USR-...
supabase secrets set SUPABASE_URL=https://xxx.supabase.co
supabase secrets set SUPABASE_SERVICE_ROLE_KEY=eyJhbG...
```

URL do webhook:
```
https://xxx.supabase.co/functions/v1/handle-mercadopago-webhook
```

### Configurar Auth Providers (opcional)

**Authentication** → **Providers** → Google/GitHub (seguir guias)

---

## 2️⃣ Mercado Pago (Pagamentos)

### Criar Aplicação

1. [https://www.mercadopago.com.br/developers/panel/app](https://www.mercadopago.com.br/developers/panel/app)
2. **Criar aplicação** → Nome: **DocSplit**
3. Produto: **Checkout Pro**

### Copiar Credenciais

**Credenciais de produção**:
- Access Token: `APP_USR-...`
- Public Key: `APP_USR-...`

Adicione no `.env`:

```bash
MERCADOPAGO_ACCESS_TOKEN=APP_USR-...
MERCADOPAGO_PUBLIC_KEY=APP_USR-...
```

### Configurar Webhook

**Seus aplicativos** → Sua app → **Webhooks**:
- URL: `https://xxx.supabase.co/functions/v1/handle-mercadopago-webhook`
- Eventos: **Pagamentos** (payments)
- **Salvar**

---

## 3️⃣ Backend (Railway)

### Criar Projeto

1. [https://railway.app](https://railway.app)
2. **New Project** → **Deploy from GitHub**
3. Conecte repo (fork `Sbarros82/DocSplit` se necessário)
4. Railway detecta `Dockerfile` ou Python

### Configurar Variáveis

**Variables**:

```bash
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbG...
MERCADOPAGO_ACCESS_TOKEN=APP_USR-...
MERCADOPAGO_PUBLIC_KEY=APP_USR-...
FRONTEND_URL=https://docsplit.vercel.app
OPENROUTER_API_KEY=sk-or-v1-... (opcional)
```

### Gerar Domínio

**Settings** → **Networking** → **Generate Domain**

URL: `https://docsplit-api.railway.app`

Salve para usar no frontend!

---

## 4️⃣ Frontend (Vercel)

### Preparar Build

```powershell
cd d:\Snap\frontend
npm install
```

Criar `.env.production`:

```bash
VITE_SUPABASE_URL=https://xxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbG...
VITE_BACKEND_URL=https://docsplit-api.railway.app
VITE_MERCADOPAGO_PUBLIC_KEY=APP_USR-...
```

### Deploy

```powershell
npm install -g vercel
vercel login
cd d:\Snap\frontend
vercel --prod
```

Responda:
- Project name: `docsplit`
- Directory: `.` (raiz)

URL final: `https://docsplit.vercel.app`

### Configurar Variáveis na Vercel (alternativa)

Painel Vercel → Projeto → **Settings** → **Environment Variables**:
- Adicione as mesmas variáveis do `.env.production`
- Marque **Production, Preview, Development**

Redeploy: `vercel --prod`

---

## 5️⃣ Domínio Personalizado (opcional)

### Comprar Domínio

Registro.br ou Hostinger: `docsplit.com.br`

### Configurar DNS

#### Frontend (Vercel)

Vercel → **Domains** → Adicionar domínio:
- `docsplit.com.br` → CNAME `cname.vercel-dns.com`
- `www.docsplit.com.br` → CNAME `cname.vercel-dns.com`

#### Backend (Railway)

Railway → **Settings** → **Domains** → Custom Domain:
- `api.docsplit.com.br` → CNAME fornecido pelo Railway

Aguarde propagação DNS (~30min a 24h)

---

## 6️⃣ Teste Completo

### 1. Cadastro

- Acesse `https://docsplit.vercel.app`
- **Criar conta** (email/senha ou Google)
- Confirme email

### 2. Verificar usuário no Supabase

**Table Editor** → **users** → deve aparecer sua linha

### 3. Comprar créditos (Sandbox)

- **Adicionar créditos** → escolha **R$ 5**
- Checkout Mercado Pago abre
- Cartão de teste:
  ```
  5031 4332 1540 6351
  CVV: 123
  Validade: 11/25
  Nome: APRO
  ```
- Confirme

### 4. Verificar webhook

**Supabase** → **Edge Functions** → **handle-mercadopago-webhook** → **Logs**

Deve aparecer:
```
✅ 50 MB adicionados para o usuário xxx
```

### 5. Verificar créditos

**Table Editor** → **users** → `total_credits_mb = 50`

Dashboard deve mostrar **50 MB disponíveis**

### 6. Processar PDF

- Upload um PDF pequeno
- Sistema desconta créditos
- Baixa ZIP gerado

**Table Editor** → **jobs** → deve aparecer registro

---

## 7️⃣ SEO (após deploy)

### Google Search Console

1. [https://search.google.com/search-console](https://search.google.com/search-console)
2. **Adicionar propriedade** → `https://docsplit.vercel.app`
3. Verificar via meta tag ou DNS
4. **Sitemap** → `https://docsplit.vercel.app/sitemap.xml` (criar depois)

### Google Analytics

1. [https://analytics.google.com](https://analytics.google.com)
2. Criar propriedade → Web
3. Copiar Measurement ID: `G-XXXXXXXXXX`
4. Adicionar no `index.html`:

```html
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

---

## 8️⃣ Monitoramento

### Logs Backend (Railway)

**Deployments** → Latest → **View Logs**

### Logs Webhook (Supabase)

**Edge Functions** → **handle-mercadopago-webhook** → **Logs**

### Banco de Dados (Supabase)

**Table Editor**:
- `users` → saldo de créditos
- `transactions` → histórico de compras
- `jobs` → uploads

### Mercado Pago

**Atividades** → **Pagamentos** → status de cada transação

---

## 9️⃣ Custos Mensais (Estimativa)

| Serviço | Plano | Custo |
|---------|-------|-------|
| Supabase | Free (até 500MB) | R$ 0 |
| Railway | Hobby ($5/mês) | R$ 25 |
| Vercel | Free (100GB banda) | R$ 0 |
| Domínio | .com.br | R$ 40/ano (R$ 3/mês) |
| **Total** | | **~R$ 28/mês** |

**Mercado Pago**: taxa de 4,99% + R$ 0,40 por transação (descontado do valor recebido)

---

## 🎉 Pronto!

Stack completa rodando:
- ✅ Frontend React responsivo (Vercel)
- ✅ Backend FastAPI + OCR (Railway)
- ✅ Auth + banco PostgreSQL (Supabase)
- ✅ Pagamentos PIX/cartão (Mercado Pago)
- ✅ Sistema de créditos funcionando
- ✅ Webhook automático

**Próximos passos:**
1. Criar blog com artigos SEO
2. Campanha Google Ads (R$ 100/mês teste)
3. Email marketing (boas-vindas + lembrete créditos)
4. Programa de afiliados

**Receita estimada em 6 meses:** R$ 600-1.500/mês  
**Receita estimada em 12 meses:** R$ 5.000-15.000/mês

Boa sorte! 🚀
