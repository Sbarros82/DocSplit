# Deploy Frontend no Vercel (Interface Web)

## Passo a Passo

### 1. Commit e Push do Frontend

```powershell
cd d:\Snap
git add .
git commit -m "feat: adiciona frontend React com Supabase e Mercado Pago"
git push origin main
```

### 2. Importar Projeto no Vercel

1. Acesse: https://vercel.com/new
2. Faça login com sua conta GitHub
3. Clique em **"Import Git Repository"**
4. Selecione o repositório **DocSplit**
5. Configure:

**Framework Preset:** Vite
**Root Directory:** `frontend`
**Build Command:** `npm run build`
**Output Directory:** `dist`

### 3. Configurar Variáveis de Ambiente

Na página de configuração do projeto, adicione as variáveis:

| Nome | Valor |
|------|-------|
| `VITE_SUPABASE_URL` | `https://pjryxiwzpfbypawxgios.supabase.co` |
| `VITE_SUPABASE_ANON_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBqcnl4aXd6cGZieXBhd3hnaW9zIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODcwNzM2NzIsImV4cCI6MjEwMjY0OTY3Mn0.d3kIGnBFJxMPIEDVY6VhZcEr0-3Gwek4KLn5W2Tc8bQ` |
| `VITE_BACKEND_URL` | `http://localhost:8000` *(temporário, atualizaremos depois do deploy do backend)* |
| `VITE_MERCADOPAGO_PUBLIC_KEY` | *(deixe em branco por enquanto)* |

### 4. Deploy

1. Clique em **"Deploy"**
2. Aguarde o build (2-5 minutos)
3. Copie a URL gerada (exemplo: `https://doc-split-xxx.vercel.app`)

### 5. Voltar ao Mercado Pago

Agora que tem a URL, volte para: https://developers.mercadopago.com/panel/app

1. **URL de redirecionamento:** `https://seu-app.vercel.app/dashboard`
2. Clique em **"Continuar"**
3. Copie as credenciais (Access Token e Public Key)

---

## Próximos Passos

Depois do deploy:

1. ✅ Copiar URL do Vercel
2. ✅ Voltar ao Mercado Pago e configurar URL
3. ✅ Copiar credenciais do Mercado Pago
4. ⏳ Deploy do backend no Railway
5. ⏳ Atualizar `VITE_BACKEND_URL` no Vercel

---

## Comandos Git para Commit

```powershell
cd d:\Snap
git add .
git commit -m "feat: adiciona frontend React com Supabase e Mercado Pago"
git push origin main
```

**Depois disso, acesse https://vercel.com/new e importe o repositório!**
