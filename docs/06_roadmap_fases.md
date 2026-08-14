# Roadmap de Desenvolvimento

Trabalhe **uma fase por vez** no Cursor. Ao final de cada fase, rode os
testes daquela fase antes de avançar. Não peça pro Cursor pular fases —
contexto pequeno e focado gera código mais confiável.

## Fase 0 — Setup do projeto (30 min)
- Criar a estrutura de pastas de `03_estrutura_projeto.md`.
- `requirements.txt` + ambiente virtual.
- Instalar dependências de sistema (poppler, tesseract).
- Prompt sugerido para o Cursor:
  > "Crie a estrutura de pastas descrita em docs/03_estrutura_projeto.md,
  > com arquivos vazios contendo apenas docstring de propósito de cada
  > módulo, conforme docs/04_especificacao_modulos.md."

## Fase 1 — Ingestão + OCR (`ingest.py`, `preprocess.py`, `ocr.py`)
- Implementar `ingest.py`: abrir PDF, renderizar páginas como imagem,
  extrair texto nativo quando existir.
- Implementar `ocr.py` chamando Tesseract.
- Testar com o PDF de exemplo: conferir visualmente se o texto extraído
  bate com o conteúdo real de 3-4 páginas variadas (uma boa, uma torta,
  uma com foto de mão no meio).
- **Critério de aceite:** rodar `ingest + ocr` no PDF de exemplo e imprimir
  o texto de cada página sem erro.

## Fase 2 — Regras de classificação (`rules.py`, `classify.py` sem LLM ainda)
- Implementar o dicionário de `05_regras_classificacao.md`.
- Implementar `classify.py` chamando só `rules.apply_rules()` por enquanto
  (sem fallback de LLM ainda — deixar `TODO`).
- **Critério de aceite:** rodar no PDF de exemplo e conferir manualmente
  a % de páginas classificadas com confiança alta (meta inicial: 70%+).

## Fase 3 — Agrupamento (`group.py`)
- Implementar as regras de agrupamento.
- **Critério de aceite:** número de grupos gerados deve ser próximo do
  esperado manualmente (ver README — ~34 grupos a partir de 46 páginas no
  PDF de exemplo).

## Fase 4 — Geração de saída (`naming.py`, `export.py`, `index_report.py`)
- Implementar geração dos PDFs finais e do índice.
- **Critério de aceite:** soma de páginas dos arquivos gerados == total de
  páginas do PDF original (validação automática, não manual).

## Fase 5 — `pipeline.py` + `cli.py`
- Orquestrar tudo, expor `python cli.py entrada.pdf saida/`.
- **Critério de aceite:** rodar o comando ponta a ponta no PDF de exemplo
  e obter a pasta de saída completa sem intervenção manual.

## Fase 6 — Fallback com LLM (`llm_classify.py`)
- Só começar esta fase depois que as Fases 1-5 estiverem funcionando com
  regras apenas — assim você sabe exatamente quantas páginas realmente
  precisam do LLM.
- Implementar a chamada à API Anthropic usando o prompt de
  `07_prompts_llm.md`.
- Plugar como fallback em `classify.py` (remover o `TODO` da Fase 2).
- **Critério de aceite:** páginas que antes ficavam sem classificação
  agora recebem `doc_type` com `source="llm"` e `confidence` razoável.

## Fase 7 — Testes automatizados
- `pytest` cobrindo cada módulo com o PDF de exemplo como fixture.
- Testes de regressão: garantir que mudanças futuras nas regras não quebram
  a classificação de tipos já conhecidos.

## Fase 8 — Interface (opcional)
- `streamlit` simples: upload → progress → download do zip + tabela do
  índice.
- Só fazer depois que o pipeline via linha de comando estiver estável —
  interface é a parte mais fácil de refazer depois.

## Dica geral para uso do Cursor

Ao pedir implementação de um módulo, cole no chat:
1. O trecho relevante de `04_especificacao_modulos.md` (contrato do módulo).
2. O critério de aceite da fase correspondente.
3. Peça explicitamente: "não implemente outros módulos, só este; use os
   schemas de `schemas.py` como estão definidos."

Isso evita que o Cursor "invente" um formato de dado diferente do
combinado entre os estágios do pipeline.
