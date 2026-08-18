# Setup Supabase CLI — Passo a Passo

## 1️⃣ Pegar Access Token

1. Acesse: [https://supabase.com/dashboard/account/tokens](https://supabase.com/dashboard/account/tokens)
2. **Generate new token**
3. Nome: `DocSplit CLI`
4. Copie o token: `sbp_...`

---

## 2️⃣ Fazer Login

```powershell
$env:SUPABASE_ACCESS_TOKEN="sbp_seu-token-aqui"
npx supabase login
```

Ou (alternativa):

```powershell
npx supabase login --token sbp_seu-token-aqui
```

---

## 3️⃣ Link ao Projeto

```powershell
cd d:\Snap
npx supabase link --project-ref pjryxiwzpfbypawxgios
```

---

## 4️⃣ Deploy Edge Function (Webhook)

```powershell
npx supabase functions deploy handle-mercadopago-webhook
```

---

## 5️⃣ Configurar Secrets

```powershell
npx supabase secrets set MERCADOPAGO_ACCESS_TOKEN=TEST-sua-chave
npx supabase secrets set SUPABASE_URL=https://pjryxiwzpfbypawxgios.supabase.co
npx supabase secrets set SUPABASE_SERVICE_ROLE_KEY=sua-service-role-key
```

---

## ✅ Pronto!

URL do webhook estará em:
```
https://pjryxiwzpfbypawxgios.supabase.co/functions/v1/handle-mercadopago-webhook
```

Configure essa URL no painel do Mercado Pago.
