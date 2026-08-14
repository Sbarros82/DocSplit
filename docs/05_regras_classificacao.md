# Regras de Classificação

## Formato de uma regra

```python
Rule(
    doc_type="viasat_fatura",
    patterns=["viasat", "viasat brasil serviços de comunicações"],
    supplier_pattern=r"Viasat",         # regex opcional para extrair o fornecedor
    confidence=0.95,
)
```

- `patterns`: lista de strings/regex (case-insensitive) que, se encontradas
  no texto da página, indicam esse tipo de documento.
- `confidence`: quão certo o sistema fica ao bater esse padrão. Padrões
  muito específicos (nome de empresa exato) → confiança alta (0.9+).
  Padrões genéricos ("comprovante", "pagamento") → confiança mais baixa
  (0.5–0.7), porque podem aparecer em vários tipos de documento diferentes.

## Exemplos derivados do caso real (comprovantes financeiros PJ rural)

| doc_type | padrões de exemplo | observação |
|---|---|---|
| `planilha_movimento_caixa` | "movimento de caixa", "entrada/saída" | geralmente a primeira página |
| `viasat_fatura` | "viasat" | fatura + comprovante + NF sempre juntos (3-4 páginas) |
| `pix_comprovante` | "comprovante de transferência", "pix por chave", "pix por dados da conta" | 1 página, nome do favorecido no texto |
| `pix_qrcode_comprovante` | "comprovante de pagamento", "qr code pix" | variação do PIX |
| `boleto_outros_bancos` | "comprovante de pagamento outros bancos" | costuma vir em 2 páginas ("1 de 2" / "2 de 2") |
| `darf` | "documento de arrecadação", "darf", "receita federal" | imposto federal |
| `fgts_guia` | "gfd", "guia do fgts digital", "fgts digital" | pode vir com página extra de "detalhe da guia" |
| `folha_pagamento` | "extrato mensal", "folha mensal" | atenção: pode aparecer duplicado (2ª via) no mesmo lote |
| `nfe` | "nf-e", "danfe", "documento auxiliar da nota fiscal" | tem CNPJ do emitente — útil para extrair fornecedor |
| `conta_energia` | "danfe", "neoenergia", "coelba", "energia elétrica" | verificar antes da regra genérica de NF-e |
| `imposto_municipal` | "prefeitura de", "duam", "documento único de arrecadação municipal" | |
| `ipva` | "ipva", "dar/cb" | |

## Como extrair o fornecedor (supplier)

Usar regex sobre campos comuns nos documentos brasileiros:
- `"Nome do beneficiário:\s*(.+)"` (comprovantes PIX/boleto)
- `"Razão Social do beneficiário:\s*(.+)"`
- `"CNPJ[:\s]*([\d./-]+)"` — útil como identificador único mais confiável
  que o nome (nomes têm variação de grafia).

## Detecção de continuação de documento

Padrões que indicam "esta página é continuação da anterior, não um novo
documento":
- `"\d de \d"` (ex: "1 de 2", "2 de 2")
- `"página \d/\d"` ou `"\d/\d"` isolado próximo ao topo
- Mesmo CNPJ do beneficiário/fornecedor da página anterior
- Ausência de qualquer cabeçalho novo reconhecido pelas regras

## Manutenção

Este dicionário deve crescer com o uso: toda vez que uma página cair no
fallback de LLM e for confirmada manualmente, considerar adicionar uma nova
regra em `rules.py` para os próximos lotes não precisarem mais chamar o LLM
para aquele tipo de documento.
