# Stack e Dependências

## Linguagem

**Python 3.11+** — escolhida porque tem biblioteca madura para cada etapa do
pipeline (PDF, OCR, dados, e chamadas de API de LLM), e é a linguagem com
mais exemplos/suporte para esse tipo de tarefa, o que ajuda o Cursor a gerar
código correto.

## Dependências por etapa

### Manipulação de PDF
- `pypdf` — dividir, juntar, ler metadados de páginas. Leve, puro Python.
- `pdf2image` — converte páginas em imagens PNG/JPEG para o OCR
  (requer `poppler-utils` instalado no sistema).

### OCR
- `pytesseract` + Tesseract OCR (binário do sistema) — gratuito, roda local.
  - Idioma: instalar o pacote de português (`tesseract-ocr-por`).
- Alternativa (melhor qualidade, mas paga): Google Document AI ou
  AWS Textract — considerar se a taxa de erro do Tesseract nos scans reais
  for muito alta (documentos tortos, fotos de celular, etc.).

### Pré-processamento de imagem (melhora OCR)
- `opencv-python` ou `Pillow` — deskew (corrigir rotação), aumento de
  contraste, remoção de ruído antes do OCR.

### Classificação com LLM (fallback)
- `anthropic` (SDK oficial) — chamadas à API do Claude para os casos que as
  regras não resolveram.

### Dados e saída
- `pandas` — montar o índice/planilha final (CSV ou XLSX).
- `pydantic` — validar o formato de dado que passa entre os estágios do
  pipeline (schemas em `04_especificacao_modulos.md`).

### Interface (opcional, fase posterior)
- `streamlit` — tela simples de upload → processamento → download.
- Ou `fastapi` + `uvicorn` se for virar um serviço/API.

### Testes
- `pytest` — testes unitários por módulo.

## requirements.txt sugerido

Ver arquivo `requirements.txt` na raiz do projeto.

## Dependências de sistema (fora do pip)

Instalar via apt (Ubuntu/Debian) ou equivalente:

```bash
sudo apt-get install -y poppler-utils tesseract-ocr tesseract-ocr-por
```

## Variáveis de ambiente

```
ANTHROPIC_API_KEY=...        # necessária apenas se usar o fallback de LLM
CLASSIFICATION_CONFIDENCE_THRESHOLD=0.8   # limiar regra vs. LLM
```
