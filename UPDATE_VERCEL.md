# Atualizar Frontend no Vercel

## 🎯 Objetivo

Conectar o frontend (Vercel) ao backend (Fly.io) que acabou de ser deployado.

---

## 📝 Passo a Passo

### 1️⃣ Acessar Configurações do Vercel

1. Acesse: **https://vercel.com/sbarros82/doc-split/settings/environment-variables**
2. Você verá a lista de variáveis de ambiente

### 2️⃣ Editar VITE_BACKEND_URL

1. Encontre a variável **`VITE_BACKEND_URL`**
2. Clique no botão **"Edit"** (ícone de lápis)
3. **Valor atual:** `http://localhost:8000`
4. **Novo valor:** `https://docsplit.fly.dev`
5. Clique em **"Save"**

### 3️⃣ Editar VITE_MERCADOPAGO_PUBLIC_KEY (Se Existir)

1. Encontre a variável **`VITE_MERCADOPAGO_PUBLIC_KEY`**
2. Se estiver vazia ou com valor temporário, edite para:
   - **Valor:** `TEST-3122cb01-0316-4dc4-a303-af31df838799`
3. Clique em **"Save"**

### 4️⃣ Redeploy do Frontend

1. Vá para: **https://vercel.com/sbarros82/doc-split**
2. Clique na aba **"Deployments"**
3. Encontre o último deployment (topo da lista)
4. Clique nos **3 pontinhos** (`⋯`) no lado direito
5. Clique em **"Redeploy"**
6. Confirme clicando em **"Redeploy"** novamente
7. Aguarde 2-3 minutos

---

## ✅ Testar Após Redeploy

Depois do redeploy, teste:

### Frontend:
**https://doc-split-beta.vercel.app**

- ✅ Página deve carregar normalmente
- ✅ Tente fazer login/cadastro (Supabase)
- ✅ Vá na página de preços
- ✅ Dashboard deve mostrar seus créditos

### Backend (direto):
**https://docsplit.fly.dev/health**

- ✅ Deve retornar JSON com tudo "true"

---

## 🎯 Status Geral

| Item | Status | URL |
|------|--------|-----|
| **Backend** | ✅ Online | https://docsplit.fly.dev |
| **Frontend** | ⏳ Precisa atualizar | https://doc-split-beta.vercel.app |
| **Supabase** | ✅ Conectado | https://pjryxiwzpfbypawxgios.supabase.co |
| **Mercado Pago** | ✅ Configurado | App ID: 2185639579586130 |

---

## 📋 Próximos Passos (Depois de Atualizar o Frontend)

1. ⏳ Deploy Edge Function (webhook) no Supabase
2. ⏳ Configurar webhook no Mercado Pago
3. ⏳ Testar pagamento end-to-end
4. ✅ **Sistema 100% funcional!**

---

**Me avise quando terminar o redeploy do Vercel para continuarmos!** 🚀
