# Arquitetura

## Pipeline (visão de alto nível)

```
PDF de entrada
    │
    ▼
[1. Ingestão]      -> converte cada página em imagem + tenta extrair texto nativo
    │
    ▼
[2. OCR]           -> para páginas sem texto nativo confiável, roda OCR
    │
    ▼
[3. Classificação] -> identifica o tipo de documento de cada página
    │                 (regras primeiro, LLM como fallback)
    ▼
[4. Agrupamento]   -> decide quais páginas consecutivas formam 1 documento
    │
    ▼
[5. Geração]       -> gera 1 PDF por grupo + nome de arquivo padronizado
    │
    ▼
[6. Índice]        -> gera planilha/CSV com o resumo de tudo que foi processado
    │
    ▼
Saída: pasta com PDFs separados + índice.csv (+ zip opcional)
```

## Princípios de design

1. **Regras antes de LLM.** Fornecedores e tipos de documento tendem a se
   repetir mês a mês (mesma empresa, mesmos boletos). Resolver por
   regex/palavra-chave é mais barato, mais rápido e 100% determinístico.
   O LLM só entra quando a regra não bate com confiança suficiente.

2. **Pipeline em estágios, não uma função gigante.** Cada estágio (OCR,
   classificação, agrupamento, geração) deve poder ser testado e depurado
   isoladamente, com formato de dado bem definido entre eles (ver
   `04_especificacao_modulos.md`).

3. **Nada de decisão silenciosa.** Toda página que fica com baixa confiança
   na classificação deve ser marcada como `revisar_manual = True` no índice
   final, nunca "adivinhada" sem rastro.

4. **Idempotência.** Rodar o mesmo PDF duas vezes deve gerar o mesmo
   resultado (nomes de arquivo determinísticos, sem timestamps aleatórios
   no nome).

5. **Custo de LLM sob controle.** Cache de classificação por hash de texto
   de página, para não pagar de novo pela mesma página se o pipeline for
   reprocessado.

## Fluxo de decisão da classificação (estágio 3+4)

```
Para cada página:
    texto = ocr_ou_texto_nativo(pagina)
    match = aplicar_regras(texto)          # dicionário de padrões (docs/05)

    se match.confianca >= LIMIAR:
        tipo_pagina = match.tipo
    senão:
        tipo_pagina = classificar_com_llm(texto)   # fallback (docs/07)

Para cada página, na ordem:
    se tipo_pagina == tipo_da_pagina_anterior
       E (mesmo_fornecedor OU texto_contém "página X de Y" OU sem_cabecalho_novo):
        agrupar com documento anterior
    senão:
        iniciar novo documento
```

## Por que não usar só LLM para tudo?

Funcionaria, mas:
- Custa por página processada (46 páginas x 12 meses = 552 chamadas/ano só
  de classificação, mais se reprocessar).
- É mais lento (chamada de API vs. regex local).
- É não-determinístico entre execuções, dificultando testes automatizados.

O modelo híbrido (regras + fallback de LLM) cobre a maioria dos casos com
regra, e usa LLM só para o que é genuinamente novo/ambíguo — bom equilíbrio
entre custo, velocidade e robustez.
