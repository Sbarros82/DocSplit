# Estrutura do Projeto

```
pdf-splitter/
├── README.md
├── .cursorrules
├── requirements.txt
├── .env.example
│
├── docs/                        # esta documentação
│
├── src/
│   └── pdf_splitter/
│       ├── __init__.py
│       │
│       ├── ingest.py            # abre o PDF, extrai páginas como imagem/texto nativo
│       ├── ocr.py                # roda OCR nas páginas sem texto confiável
│       ├── preprocess.py        # deskew, contraste, limpeza de imagem
│       │
│       ├── rules.py              # dicionário de regras de classificação
│       ├── classify.py           # aplica regras; chama llm_classify quando preciso
│       ├── llm_classify.py       # chamadas à API Anthropic (fallback)
│       │
│       ├── group.py              # agrupa páginas consecutivas em documentos
│       ├── naming.py             # gera nomes de arquivo padronizados
│       │
│       ├── export.py             # gera os PDFs finais + zip
│       ├── index_report.py       # gera o CSV/planilha índice
│       │
│       ├── schemas.py            # modelos pydantic (Page, Document, ClassificationResult...)
│       ├── config.py             # configurações (limiares, caminhos, idioma OCR)
│       └── pipeline.py           # orquestra tudo (chama os estágios em ordem)
│
├── cli.py                        # ponto de entrada: `python cli.py entrada.pdf saida/`
│
├── app_streamlit.py              # (fase posterior) interface web simples
│
├── tests/
│   ├── fixtures/                 # PDFs de exemplo para teste
│   ├── test_ingest.py
│   ├── test_ocr.py
│   ├── test_classify.py
│   ├── test_group.py
│   └── test_export.py
│
└── data/
    ├── input/                    # PDFs a processar (não versionar conteúdo real)
    └── output/                   # resultados gerados
```

## Convenções

- Cada módulo em `src/pdf_splitter/` tem **uma responsabilidade só** (ver
  contrato exato em `04_especificacao_modulos.md`).
- `pipeline.py` é o único lugar que conhece a ordem dos estágios — os
  módulos individuais não devem chamar uns aos outros diretamente, exceto
  `classify.py` chamando `llm_classify.py` como fallback interno.
- Dados reais de clientes (PDFs de exemplo, comprovantes) **nunca vão para o
  git** — usar `.gitignore` para `data/input/` e `data/output/`. Só fixtures
  anonimizadas ficam em `tests/fixtures/`.
