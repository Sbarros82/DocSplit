# Setup Supabase + Mercado Pago

Guia passo a passo para configurar o banco de dados e pagamentos.

## 1. Criar Projeto no Supabase

1. Acesse [https://supabase.com](https://supabase.com)
2. **New Project**
3. Preencha:
   - **Name**: docsplit-prod
   - **Database Password**: gere uma senha forte (salve!)
   - **Region**: South America (São Paulo)
4. Aguarde ~2 minutos

---

## 2. Executar Schema SQL

1. No painel do Supabase, vá em **SQL Editor**
2. **New query**
3. Cole todo o conteúdo de `d:\Snap\supabase\schema.sql`
4. **Run** (botão verde)
5. Aguarde sucesso ✅

Isso cria:
- Tabelas: `users`, `transactions`, `jobs`
- Funções: `get_available_credits`, `consume_credits`
- RLS (Row Level Security)
- Triggers automáticos

---

## 3. Configurar Auth Providers

### Email/Senha (padrão, já ativo)

### Google OAuth (opcional, recomendado)

1. **Authentication** → **Providers** → **Google**
2. **Enabled** → ON
3. Siga o guia para criar OAuth app no Google Console
4. Cole Client ID e Secret
5. **Save**

### GitHub OAuth (opcional)

1. **Authentication** → **Providers** → **GitHub**
2. Siga o mesmo processo

---

## 4. Copiar Credenciais

1. **Settings** → **API**
2. Copie:
   - **Project URL**: `https://xxx.supabase.co`
   - **anon public key**: `eyJhbGc...` (cliente frontend)
   - **service_role key**: `eyJhbGc...` (backend, NUNCA expor)

3. Adicione no `.env`:

```bash
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_ANON_KEY=eyJhbG...sua-anon-key
SUPABASE_SERVICE_ROLE_KEY=eyJhbG...sua-service-role-key
```

---

## 5. Deploy Edge Function (Webhook)

### Instalar Supabase CLI

```powershell
npm install -g supabase
```

### Login

```powershell
supabase login
```

### Linkar projeto

```powershell
cd d:\Snap
supabase link --project-ref SEU_PROJECT_REF
```

(Project ref está na URL: `https://SEU_PROJECT_REF.supabase.co`)

### Deploy função

```powershell
supabase functions deploy handle-mercadopago-webhook
```

### Configurar secrets

```powershell
supabase secrets set MERCADOPAGO_ACCESS_TOKEN=APP_USR-sua-chave
supabase secrets set SUPABASE_URL=https://seu-projeto.supabase.co
supabase secrets set SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...
```

### URL do webhook

Após deploy, a URL será:
```
https://seu-projeto.supabase.co/functions/v1/handle-mercadopago-webhook
```

---

## 6. Criar Aplicação no Mercado Pago

### Produção

1. Acesse [https://www.mercadopago.com.br/developers/panel/app](https://www.mercadopago.com.br/developers/panel/app)
2. **Criar aplicação**
3. Nome: **DocSplit**
4. Produto integrado: **Checkout Pro**
5. **Criar aplicação**

### Copiar credenciais

1. Vá em **Credenciais de produção**
2. Copie:
   - **Access Token**: `APP_USR-...`
   - **Public Key**: `APP_USR-...`

3. Adicione no `.env`:

```bash
MERCADOPAGO_ACCESS_TOKEN=APP_USR-sua-chave-producao
MERCADOPAGO_PUBLIC_KEY=APP_USR-sua-public-key
```

### Sandbox (testes)

1. **Credenciais de teste**
2. Copie Token de teste
3. Use para desenvolvimento:

```bash
MERCADOPAGO_ACCESS_TOKEN=TEST-sua-chave-teste
MERCADOPAGO_PUBLIC_KEY=TEST-sua-public-key-teste
```

---

## 7. Configurar Webhook no Mercado Pago

1. No painel do Mercado Pago: **Seus aplicativos** → Sua app → **Webhooks**
2. **Nova URL de notificação**
3. Cole a URL da Edge Function:
   ```
   https://seu-projeto.supabase.co/functions/v1/handle-mercadopago-webhook
   ```
4. Eventos: **Pagamentos** (payments)
5. **Salvar**

### Testar webhook

1. Faça um pagamento de teste
2. Veja logs no Supabase:
   - **Edge Functions** → **handle-mercadopago-webhook** → **Logs**
3. Verifique se créditos foram adicionados:
   - **Table Editor** → **transactions**
   - **Table Editor** → **users** (coluna `total_credits_mb`)

---

## 8. Configurar CORS (se necessário)

Se o frontend estiver em domínio diferente do backend:

1. Supabase: **Settings** → **API** → **CORS**
2. Adicione domínio do frontend:
   ```
   https://docsplit.vercel.app
   ```

---

## 9. Variáveis de Ambiente — Resumo

### Frontend (Vercel)

```bash
VITE_SUPABASE_URL=https://seu-projeto.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbG...anon-key
VITE_BACKEND_URL=https://docsplit-api.railway.app
VITE_MERCADOPAGO_PUBLIC_KEY=APP_USR-sua-public-key
```

### Backend (Railway)

```bash
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbG...service-role (NUNCA a anon!)
MERCADOPAGO_ACCESS_TOKEN=APP_USR-sua-access-token
MERCADOPAGO_PUBLIC_KEY=APP_USR-sua-public-key
FRONTEND_URL=https://docsplit.vercel.app
OPENROUTER_API_KEY=sk-or-v1-... (opcional)
```

### Edge Function (Supabase)

```bash
# Já configurado via supabase secrets set
MERCADOPAGO_ACCESS_TOKEN=APP_USR-...
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbG...
```

---

## 10. Testar Fluxo Completo

### 1. Cadastro

- Acesse frontend
- Clique **Criar conta**
- Use email + senha OU Google/GitHub
- Confirme email (se email/senha)

### 2. Verificar usuário criado

- Supabase → **Table Editor** → **users**
- Deve aparecer sua linha com `total_credits_mb = 0`

### 3. Comprar créditos (Sandbox)

- Clique **Adicionar créditos**
- Escolha pacote (ex: R$ 5 = 50 MB)
- Checkout Mercado Pago abre
- Use cartão de teste:
  ```
  Número: 5031 4332 1540 6351
  CVV: 123
  Validade: 11/25
  Nome: APRO (aprova sempre)
  CPF: 123.456.789-00
  ```
- Confirme pagamento

### 4. Webhook processa

- Aguarde ~5-10 segundos
- Supabase Edge Function recebe notificação
- Adiciona créditos em `users.total_credits_mb`
- Cria registro em `transactions`

### 5. Verificar créditos

- Recarregue dashboard
- Deve aparecer **50 MB disponíveis**

### 6. Processar PDF

- Upload um PDF
- Sistema desconta créditos
- Cria registro em `jobs`
- Atualiza `users.used_credits_mb`

---

## 11. Monitoramento

### Logs do Webhook

**Supabase** → **Edge Functions** → **handle-mercadopago-webhook** → **Logs**

### Tabelas

- **users**: saldo de créditos
- **transactions**: histórico de compras
- **jobs**: uploads processados

### Mercado Pago

**Atividades** → **Pagamentos** → ver status de cada transação

---

## Troubleshooting

### Webhook não dispara

- Verifique URL no painel Mercado Pago
- Teste manualmente: `curl -X POST https://sua-function.supabase.co/functions/v1/handle-mercadopago-webhook`
- Veja logs da Edge Function

### Créditos não foram adicionados

- Veja logs da Edge Function
- Verifique se `user_id` está no `metadata` do pagamento
- Confirme que `payment_status = 'approved'`

### "SUPABASE_URL não definida"

- Verifique `.env` no backend
- No Railway: **Variables** → adicione manualmente
- Redeploy após adicionar variável

---

## Pronto!

Stack completa configurada:
- ✅ Supabase (banco + auth)
- ✅ Mercado Pago (pagamentos)
- ✅ Webhook automático
- ✅ Sistema de créditos funcionando

**Próximo passo:** deploy do frontend (Vercel) + backend (Railway)
