# Deploy Rápido — 3 opções

## 🚀 1. Vercel (mais rápido, limitado)

**Quando usar**: demonstração, PDFs pequenos (< 4 MB, < 20 páginas), sem scan/OCR

```powershell
# Instalar CLI (primeira vez)
npm install -g vercel

# Login
vercel login

# Deploy
vercel --prod
```

✅ Deploy em 2 minutos  
❌ Sem OCR (só texto nativo do PDF)  
❌ Limite 4 MB upload  
❌ Timeout 60 segundos

**IMPORTANTE**: Não precisa de banco de dados! O sistema não guarda nada.

---

## 🎯 2. Railway (recomendado)

**Quando usar**: uso real, scans, OCR, lotes grandes (até 50 MB e 200 páginas)

1. Acesse [railway.app](https://railway.app)
2. **New Project** → **Deploy from GitHub repo**
3. Selecione seu repo (fork `Sbarros82/DocSplit` se necessário)
4. Railway detecta `Dockerfile` e instala Tesseract automaticamente
5. **Variables**:
   - `OPENROUTER_API_KEY` = `sk-or-v1-sua-chave` (opcional)
6. **Networking** → Generate domain
7. Abra a URL pública

✅ OCR completo (Tesseract em português)  
✅ 50 MB upload  
✅ 200 páginas por arquivo  
✅ Grátis até $5/mês (suficiente)

---

## 💻 3. Local (sem limites)

**Quando usar**: arquivos gigantes, muitos documentos, uso interno

```powershell
# Windows
start.bat

# PowerShell
.\run_local.ps1
```

Abre em `http://127.0.0.1:8000`

**Na mesma rede** (celular/outros PCs): `http://192.168.0.170:8000`

✅ 100 MB upload  
✅ 500 páginas  
✅ OCR completo  
✅ Sem timeout  
✅ Processamento mais rápido (hardware local)

---

## ❓ Preciso de banco de dados?

**NÃO!** O DocSplit é **stateless**:

- ✅ Recebe PDF → processa → devolve ZIP → **esquece**
- ❌ Não tem login/usuários
- ❌ Não guarda histórico
- ❌ Não armazena arquivos

**Banco só seria útil para:**
- Sistema multi-usuário com login
- Histórico de processamentos
- Armazenamento permanente de PDFs
- Fila de jobs assíncrona

Para uso como ferramenta (pontual, sob demanda), banco é **desnecessário** e só complica.

---

## 🔑 Variáveis de ambiente (todas opcionais)

| Variável | Padrão | Quando usar |
|----------|--------|-------------|
| `OPENROUTER_API_KEY` | — | Fallback de IA para páginas duvidosas |
| `OPENROUTER_MODEL` | `openai/gpt-4o-mini` | Trocar modelo (mais barato/rápido) |
| `OCR_DPI` | `180` | Qualidade OCR (180 = rápido, 300 = lento/preciso) |
| `CLASSIFICATION_CONFIDENCE_THRESHOLD` | `0.8` | Quando enviar para revisão manual |

**Na Vercel**: `vercel env add NOME_VARIAVEL`  
**No Railway**: painel **Variables**  
**Local**: arquivo `.env` na raiz

---

## 📊 Comparação rápida

| | Vercel | Railway | Local |
|---|---|---|---|
| **Deploy** | 2 min | 5 min | — |
| **OCR** | ❌ | ✅ | ✅ |
| **Upload** | 4 MB | 50 MB | 100 MB |
| **Páginas** | 20 | 200 | 500 |
| **Custo** | Grátis | $0-5/mês | Só luz |
| **Setup** | CLI | Painel web | `start.bat` |
| **Manutenção** | Zero | Zero | PC ligado |

**Recomendação**: Railway para produção, Local para lotes grandes, Vercel para demo/portfolio.
