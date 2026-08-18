# Deploy na Vercel

**O DocSplit NÃO precisa de banco de dados** — todo o processamento é stateless (sem usuários, sem histórico).

## Limitações na Vercel (plano gratuito)

| Recurso | Local | Vercel |
|---------|-------|--------|
| **Upload** | 100 MB | 4-5 MB |
| **Páginas** | 500 | 20 |
| **OCR** | ✅ Tesseract | ❌ Sem binário |
| **Timeout** | Ilimitado | 60s |
| **Memória** | Toda RAM | 1 GB |

**Resumo**: Vercel serve para **demonstração** e PDFs pequenos já digitalizados (com texto nativo). Para lotes grandes com OCR, use local ou Railway.

---

## Passo a passo

### 1. Instalar Vercel CLI

```powershell
npm install -g vercel
```

### 2. Login na Vercel

```powershell
vercel login
```

### 3. Configurar variáveis de ambiente (opcional)

Se quiser usar o fallback de IA (OpenRouter) para classificação:

```powershell
vercel env add OPENROUTER_API_KEY
```

Cole sua chave e pressione Enter. Escolha:
- **Production, Preview, Development** (todas)

**Não é obrigatório** — o sistema funciona só com regras (sem IA).

### 4. Deploy

No diretório `d:\Snap`:

```powershell
vercel --prod
```

A CLI vai perguntar:
- **Set up project?** → Yes
- **Link to existing?** → No (primeira vez)
- **Project name** → docsplit (ou o que quiser)
- **Directory** → `.` (raiz)
- **Override settings?** → No

Deploy leva ~2 minutos. No fim aparece:

```
✅  Production: https://docsplit-xxx.vercel.app
```

### 5. Testar

Abra a URL no navegador. O frontend carrega automaticamente e se conecta à API.

---

## O que acontece no deploy

1. **Frontend** (`public/`) vira site estático servido direto pelo CDN da Vercel
2. **API** (`api/index.py`) vira função serverless Python
3. A Vercel instala só as dependências de `requirements.txt` (sem OCR)
4. Todo `tempfile` funciona — cada requisição tem storage efêmero

---

## Troubleshooting

### "Module not found" no deploy

A Vercel usa Python 3.9. Se der erro, adicione `runtime: python3.9` em `vercel.json`:

```json
{
  "functions": {
    "api/index.py": {
      "runtime": "python3.9",
      "maxDuration": 60,
      "memory": 1024
    }
  }
}
```

### "Request Entity Too Large"

O upload está maior que 4 MB. Comprima o PDF ou processe localmente.

### "Function execution timed out"

PDF com muitas páginas ou OCR pesado. A Vercel tem timeout de 60s (plano pago: 300s).

---

## Banco de dados? Não precisa!

O DocSplit:
- ✅ **Stateless**: processa → devolve ZIP → esquece
- ❌ **Não tem usuários** (sem login, sem sessões persistentes)
- ❌ **Não guarda histórico** (cada job é independente)
- ❌ **Não armazena PDFs** (tudo em memória temporária)

**Supabase/Postgres só seria útil se** você quisesse:
- Login de usuários
- Histórico de processamentos
- Armazenar PDFs originais
- Queue de jobs assíncronos

Para o caso de uso atual (ferramenta de uso pontual), banco é **desnecessário** e só complica.

---

## Alternativa: Railway (mais robusto)

Se precisar de OCR e lotes grandes, deploy no **Railway** (tem Tesseract e menos limites):

1. Conecte o repo GitHub ao Railway
2. Configure buildpack Python + apt packages (`tesseract-ocr tesseract-ocr-por`)
3. Defina `OPENROUTER_API_KEY` (opcional)
4. Deploy automático a cada push

Railway é gratuito até $5/mês de uso (suficiente para uso pessoal/testes).

---

## Atualizar deploy

Após editar código:

```powershell
git add .
git commit -m "feat: melhoria X"
git push
vercel --prod
```

Ou conecte o repo no painel da Vercel para **deploy automático** a cada push na branch `main`.
