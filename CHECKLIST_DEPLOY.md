# Checklist Deploy Vercel

Antes de rodar `vercel --prod`:

## ✅ Pré-requisitos

- [ ] Node.js instalado (`node --version`)
- [ ] Git configurado e código commitado
- [ ] Conta na Vercel (gratuita) — [vercel.com/signup](https://vercel.com/signup)
- [ ] Vercel CLI instalado: `npm install -g vercel`
- [ ] Login feito: `vercel login`

## ✅ Arquivos necessários (já criados)

- [x] `vercel.json` — configuração de runtime e rotas
- [x] `requirements.txt` — dependências Python sem OCR
- [x] `.vercelignore` — ignora venv, cache, testes
- [x] `.env.example` — template de variáveis (não vai para deploy)
- [x] `api/index.py` — detecta `IS_VERCEL` e ajusta limites

## ✅ Variáveis de ambiente (opcional)

Se quiser fallback de IA:

```powershell
vercel env add OPENROUTER_API_KEY
```

Cole: `sk-or-v1-sua-chave` (OpenRouter)

Escolha: **Production, Preview, Development**

**Pode pular** — o sistema funciona só com regras (sem IA).

## ✅ Deploy

```powershell
cd d:\Snap
vercel --prod
```

Responda:
- **Set up project?** → Yes
- **Link to existing?** → No (primeira vez)
- **Project name** → `docsplit` (ou personalizado)
- **Directory** → `.` (enter)
- **Override settings?** → No

Aguarde ~2 minutos. Sucesso quando aparecer:

```
✅  Production: https://docsplit-xxx.vercel.app
```

## ✅ Testar

1. Abra `https://seu-projeto.vercel.app`
2. Arraste um PDF **pequeno** (< 3 MB, com texto nativo)
3. Clique **Separar documentos**
4. Baixe o ZIP gerado

**Teste com**:
- ✅ Boleto Itaú
- ✅ Comprovante PIX
- ✅ NF-e em PDF
- ❌ Scan sem texto (não tem OCR na Vercel)

## ✅ Após deploy

### Configurar domínio personalizado (opcional)

No painel Vercel:
1. **Settings** → **Domains**
2. Adicione seu domínio
3. Aponte DNS conforme instruções

### Deploy automático

1. No painel Vercel, **Settings** → **Git**
2. Conecte seu repo GitHub
3. Marque **Production Branch** = `main`
4. A cada `git push` → deploy automático

### Monitorar

- **Analytics**: uso, requisições, erros
- **Logs**: painel → seu projeto → **Functions**
- **Limites**: plano gratuito tem 100 GB/mês de banda

## 🚨 Problemas comuns

### Deploy falha com "Module not found"

Verifique `requirements.txt` — só pode ter pacotes Python puros (sem binários de sistema).

### "Request Entity Too Large"

Upload maior que 4 MB. Teste com PDF menor ou use Railway/local.

### "Function execution timed out"

PDF com muitas páginas. Limite Vercel: 60s (plano Pro: 300s).

### Página em branco

1. Abra DevTools (F12) → Console
2. Se aparecer erro CORS ou 404: `vercel.json` incorreto
3. Força refresh: Ctrl+Shift+R

### API não responde

Vercel pode levar 1-2 min para "acordar" cold start. Recarregue.

## 📝 Notas

- **Stateless**: cada requisição é independente (sem sessão, banco, cache)
- **Efêmero**: arquivos temporários são deletados após a resposta
- **Base64**: ZIP vem inline no JSON (< 4 MB OK)
- **Sem OCR**: só PDFs com texto nativo funcionam bem

Para OCR e lotes grandes → Railway ou local.
