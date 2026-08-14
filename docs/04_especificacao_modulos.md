# Especificação dos Módulos

Cada módulo abaixo deve ser implementado e testado isoladamente, com o
contrato de entrada/saída descrito. Os schemas usam `pydantic`.

## schemas.py — modelos de dados compartilhados

```python
class Page(BaseModel):
    page_number: int              # 1-indexed
    native_text: str | None       # texto extraído nativamente do PDF, se houver
    ocr_text: str | None          # texto obtido via OCR
    image_path: str | None        # caminho da imagem renderizada da página

class ClassificationResult(BaseModel):
    page_number: int
    doc_type: str                 # ex: "viasat_fatura", "pix_comprovante", "darf"
    supplier: str | None          # nome do fornecedor/beneficiário, se identificado
    confidence: float             # 0.0 a 1.0
    source: Literal["rule", "llm"]
    matched_pattern: str | None   # qual regra bateu (para depuração)

class DocumentGroup(BaseModel):
    doc_type: str
    supplier: str | None
    start_page: int
    end_page: int
    needs_review: bool            # True se baixa confiança em qualquer página do grupo

class ExportedFile(BaseModel):
    filename: str
    doc_type: str
    supplier: str | None
    start_page: int
    end_page: int
    output_path: str
```

## ingest.py

- **Entrada:** caminho do PDF.
- **Saída:** `list[Page]` — uma por página, com `native_text` preenchido
  quando o PDF já tem texto selecionável, e `image_path` sempre preenchido
  (renderizar todas as páginas como imagem, mesmo as com texto nativo, para
  possibilitar OCR de reforço se necessário).
- **Detalhe importante:** muitos scans desta pasta são fotos de celular
  (tortas, com sombra de dedo) — não assumir que o texto nativo do PDF é
  confiável nem que a imagem está bem enquadrada.

## preprocess.py

- **Entrada:** caminho de imagem de uma página.
- **Saída:** caminho de imagem processada (deskew, contraste ajustado,
  conversão para escala de cinza).
- Deve ser possível desabilitar via config, para comparar OCR com/sem
  pré-processamento durante o desenvolvimento.

## ocr.py

- **Entrada:** `Page` (com `image_path` preenchido).
- **Saída:** mesma `Page`, com `ocr_text` preenchido.
- Só roda OCR se `native_text` for `None` ou tiver menos de N caracteres
  (configurável) — não gastar OCR em páginas que já têm texto nativo bom.

## rules.py

- Dicionário/lista de regras (ver `05_regras_classificacao.md` para o
  formato e exemplos concretos).
- Função `apply_rules(text: str) -> ClassificationResult | None`.

## classify.py

- **Entrada:** `list[Page]`.
- **Saída:** `list[ClassificationResult]`.
- Lógica: para cada página, tenta `rules.apply_rules()`; se
  `confidence < THRESHOLD` (ou não bateu nenhuma regra), chama
  `llm_classify.classify_page()` como fallback.
- Deve cachear resultados por hash do texto da página (evitar chamar LLM de
  novo para texto idêntico já visto).

## llm_classify.py

- **Entrada:** texto de uma página (e, opcionalmente, os tipos de documento
  já vistos nas páginas vizinhas, para dar contexto de continuidade).
- **Saída:** `ClassificationResult` com `source="llm"`.
- Usa a API Anthropic. Ver prompt de referência em `07_prompts_llm.md`.
- Deve ter timeout e tratamento de erro — se a API falhar, marcar a página
  como `needs_review=True` em vez de quebrar o pipeline inteiro.

## group.py

- **Entrada:** `list[ClassificationResult]` (na ordem das páginas).
- **Saída:** `list[DocumentGroup]`.
- Regras de agrupamento (nesta ordem de prioridade):
  1. Mesmo `doc_type` E mesmo `supplier` em páginas consecutivas → mesmo grupo.
  2. Texto contém padrão de continuação (`"página 2 de 2"`, `"2/2"`,
     `"continuação"`) → mesmo grupo, mesmo que `doc_type` mude ligeiramente.
  3. Caso contrário → novo grupo.

## naming.py

- **Entrada:** `DocumentGroup`, índice sequencial.
- **Saída:** string de nome de arquivo, ex:
  `"02_viasat_fatura_julho2025.pdf"`.
- Formato: `{ordem:02d}_{doc_type}_{supplier_slug}_{data_se_houver}.pdf`
  (slug = minúsculo, sem acento, espaços viram `_`).
- Deve garantir nomes únicos mesmo se dois documentos tiverem o mesmo tipo
  e fornecedor no mesmo lote (sufixo `_via2`, `_via3` etc.).

## export.py

- **Entrada:** PDF original, `list[DocumentGroup]`, pasta de saída.
- **Saída:** um arquivo PDF por grupo na pasta de saída + (opcional) um
  `.zip` com todos.
- **Validação obrigatória:** soma das páginas de todos os grupos deve ser
  igual ao total de páginas do PDF original — se não bater, lançar erro
  explícito em vez de gerar saída incompleta silenciosamente.

## index_report.py

- **Entrada:** `list[ExportedFile]`.
- **Saída:** CSV/XLSX com colunas: arquivo, tipo de documento, fornecedor,
  páginas (ex. "8-9"), precisa revisão manual (sim/não).

## pipeline.py

- Orquestra: `ingest → preprocess (se aplicável) → ocr → classify → group →
  export → index_report`.
- Deve expor uma função única, ex. `run_pipeline(input_pdf, output_dir) ->
  list[ExportedFile]`, para ser chamada tanto pelo `cli.py` quanto por um
  futuro `app_streamlit.py`.
