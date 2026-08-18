# Atualizar VITE_BACKEND_URL no Vercel

## 📝 Passo a Passo

1. Acesse: https://vercel.com/sbarros82/doc-split/settings/environment-variables

2. Procure a variável **`VITE_BACKEND_URL`**

3. Clique em **"Edit"** (ícone de lápis)

4. **Mude o valor:**
   - De: `http://localhost:8000`
   - Para: `https://docsplit.fly.dev`

5. Clique em **"Save"**

6. **Redeploy:**
   - Vá em: https://vercel.com/sbarros82/doc-split
   - Clique na aba **"Deployments"**
   - Clique nos **3 pontinhos** do último deployment
   - Clique em **"Redeploy"**
   - Aguarde 2-3 minutos

---

## ✅ Teste Depois do Redeploy

Acesse: https://doc-split-beta.vercel.app

- Teste fazer login
- Vá em "Preços"
- Tente processar um PDF (teste com PDF pequeno)

---

## 🎯 Depois Disso

Faltam só 2 coisas:
1. Deploy do webhook no Supabase
2. Configurar webhook no Mercado Pago

**E o sistema estará 100% funcional!** 🚀
