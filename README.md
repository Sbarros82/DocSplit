# DocSplit — Separador Inteligente de Documentos

Recebe um PDF com **vários documentos misturados** (boletos, PIX, NF-e, DARF, FGTS, contas) e devolve **um PDF por documento**, já nomeado, mais um índice em Excel.

## Rodar no Windows

Dê um duplo clique em **`start.bat`**. O navegador abre em [http://127.0.0.1:8000](http://127.0.0.1:8000).

Na primeira vez o script cria o `venv` e o arquivo `.env`. Abra o `.env` e cole:

```
OPENROUTER_API_KEY=sk-or-v1-sua-chave
```

Sem essa chave o sistema ainda separa por regras; com ela, páginas duvidosas passam pelo modelo via OpenRouter.

CLI (sem interface):

```bat
venv\Scripts\python.exe cli.py data\input\arquivo.pdf data\output\resultado
```

Tesseract (OCR de scans) é opcional: `winget install UB-Mannheim.TesseractOCR` com o pacote de português.

## Railway (recomendado na nuvem)

Tem Tesseract, OCR, lotes maiores e a chave OpenRouter.

1. Em [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo** → `Sbarros82/DocSplit`.
2. O `Dockerfile` já instala Tesseract em português.
3. Em **Variables**, adicione:
   - `OPENROUTER_API_KEY` = sua chave
   - `OPENROUTER_MODEL` = `openai/gpt-4o-mini` (opcional)
4. Em **Settings → Networking**, gere um domínio público.
5. Abra a URL do Railway.

Limites no Railway: **50 MB** e **200 páginas** por arquivo.

## Vercel (só o site)

Adequado para demonstração. Sem OCR, ~4 MB e 20 páginas. A API Python está em `api/index.py`.

## API

| Método | Caminho | Uso |
|--------|---------|-----|
| GET | `/api/health` | Status, OCR, IA, limites |
| POST | `/api/process` | `multipart/form-data` campo `file` |

Documentação interna em `docs/`.
