# DocSplit — Separador Inteligente de Documentos

Recebe um PDF com **vários documentos misturados** (boletos, PIX, NF-e, DARF, FGTS, contas) e devolve **um PDF por documento**, já nomeado, mais um índice em Excel.

Funciona **no seu computador** e pode ser publicado na **Vercel** (frontend estático + API Python).

## Como usar localmente

```powershell
# na pasta do projeto
.\run_local.ps1
```

Abra [http://127.0.0.1:8000](http://127.0.0.1:8000). Arraste um PDF, clique em **Separar documentos** e baixe o ZIP.

CLI (sem interface):

```powershell
.\venv\Scripts\python.exe cli.py data\input\arquivo.pdf data\output\resultado
```

### Dependências de sistema (OCR, opcional)

O pipeline usa **texto nativo** do PDF sempre. OCR (Tesseract) só entra em páginas escaneadas sem texto.

- Tesseract com idioma português — já instalável via `winget install UB-Mannheim.TesseractOCR`
- Pacotes Python: `.\venv\Scripts\pip.exe install -r requirements-local.txt`

Sem Tesseract o sistema continua: páginas sem texto vão marcadas para **revisão manual**.

## Publicar na Vercel

1. Envie o repositório para o GitHub.
2. Em [vercel.com](https://vercel.com) → **Add New Project** → importe o repo.
3. Framework preset: **Other**. A Vercel detecta `api/index.py` e a pasta `public/`.
4. Deploy.

Na nuvem (plano Hobby):

- limite de **~4 MB** por arquivo e **20 páginas** (timeout da função);
- **sem Tesseract** — use PDFs com texto selecionável, ou processe scans grandes no modo local.

Lotes pesados de scanner continuam no `run_local.ps1`.

## API

| Método | Caminho | Uso |
|--------|---------|-----|
| GET | `/api/health` | Status, OCR, limites |
| POST | `/api/process` | `multipart/form-data` campo `file` |

## Documentação interna

Detalhes de arquitetura e regras de classificação estão em `docs/`.
