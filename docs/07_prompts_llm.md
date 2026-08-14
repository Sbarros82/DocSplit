# Prompts para o Fallback de LLM

Estes prompts são para a etapa de classificação (`llm_classify.py`), usados
**apenas** quando as regras de `05_regras_classificacao.md` não conseguem
classificar uma página com confiança suficiente.

## Prompt de classificação de página

**System / instrução:**

```
Você classifica páginas de documentos financeiros/administrativos
brasileiros (boletos, comprovantes PIX, notas fiscais, guias de imposto,
folha de pagamento, etc.).

Responda APENAS em JSON, sem texto adicional, no formato:
{
  "doc_type": "<tipo_curto_em_snake_case>",
  "supplier": "<nome do fornecedor/beneficiário ou null>",
  "confidence": <número de 0.0 a 1.0>,
  "is_continuation": <true/false>,
  "reasoning": "<explicação em uma frase curta>"
}

"is_continuation": true se esta página parece ser a continuação do mesmo
documento da página anterior (ex: "página 2 de 2", mesmo CNPJ, mesmo
beneficiário sem cabeçalho novo).

Se não conseguir identificar o tipo com razoável certeza, use
"doc_type": "desconhecido" e "confidence" baixo (< 0.5).
```

**User (montado dinamicamente pelo código):**

```
Texto extraído da página {numero_da_pagina}:
"""
{texto_ocr_ou_nativo}
"""

Tipo de documento da página anterior (se houver): {tipo_anterior}
Fornecedor da página anterior (se houver): {fornecedor_anterior}
```

## Notas de implementação

- Usar `max_tokens` baixo (a resposta é sempre um JSON pequeno).
- Fazer parsing do JSON com tratamento de erro — se o modelo devolver algo
  fora do formato esperado, tratar como `needs_review=True` em vez de
  quebrar o pipeline.
- Cachear por hash do texto da página (ver `04_especificacao_modulos.md`,
  seção `classify.py`) para não pagar duas vezes pela mesma página em
  reprocessamentos.
- Manter uma tabela local (arquivo JSON ou banco simples) com
  `doc_type` sugeridos pelo LLM ao longo do tempo — é a fonte de novas
  regras a promover para `rules.py` (ver seção "Manutenção" em
  `05_regras_classificacao.md`).

## Prompt opcional: extração de dados estruturados

Para além de classificar, se quiser já extrair valor/data/CNPJ de cada
documento para o índice final, use um segundo prompt (separado, para não
misturar responsabilidades):

```
Extraia os seguintes campos do texto do documento abaixo, respondendo
APENAS em JSON:
{
  "valor": "<valor monetário principal, ou null>",
  "data_vencimento": "<DD/MM/AAAA ou null>",
  "data_pagamento": "<DD/MM/AAAA ou null>",
  "cnpj_ou_cpf_fornecedor": "<string ou null>"
}

Texto:
"""
{texto_do_documento_completo}
"""
```

Rodar este prompt uma vez por **documento agrupado** (não por página), após
a etapa de agrupamento — assim ele já recebe o texto de todas as páginas do
mesmo documento concatenado.
