# Guia de Desenvolvimento

## Status Atual: Fase 0 ✓ Completa

A estrutura base do projeto foi criada com sucesso! 

### Estrutura Criada

```
d:\Snap\
├── docs/               # Documentação completa
├── src/
│   └── pdf_splitter/   # Código-fonte do sistema
│       ├── __init__.py
│       ├── schemas.py           ✓ Modelos Pydantic definidos
│       ├── config.py            ✓ Configurações
│       ├── ingest.py            ⏳ TODO: implementar
│       ├── preprocess.py        ⏳ TODO: implementar
│       ├── ocr.py               ⏳ TODO: implementar
│       ├── rules.py             ⏳ TODO: implementar
│       ├── classify.py          ⏳ TODO: implementar
│       ├── llm_classify.py      ⏳ TODO: implementar (Fase 6)
│       ├── group.py             ⏳ TODO: implementar
│       ├── naming.py            ⏳ TODO: implementar
│       ├── export.py            ⏳ TODO: implementar
│       ├── index_report.py      ⏳ TODO: implementar
│       └── pipeline.py          ⏳ TODO: implementar
├── tests/              # Testes automatizados
├── data/
│   ├── input/          # PDFs para processar (não versionar)
│   └── output/         # Resultados gerados (não versionar)
├── cli.py              ✓ CLI pronto (aguardando implementação dos módulos)
├── app_streamlit.py    ⏳ Fase 8 (opcional)
├── requirements.txt    ✓
├── .env.example        ✓
├── .gitignore          ✓
└── .cursorrules        ✓
```

## Próximas Etapas

### Fase 1 - Ingestão + OCR (PRÓXIMA)

1. **Instalar dependências do sistema** (requer admin no Windows):
   ```powershell
   # Poppler (para pdf2image)
   # Baixar de: https://github.com/oschwartz10612/poppler-windows/releases/
   # Extrair e adicionar ao PATH
   
   # Tesseract OCR
   # Baixar de: https://github.com/UB-Mannheim/tesseract/wiki
   # Instalar e garantir que está no PATH
   # Baixar pacote de idioma português durante instalação
   ```

2. **Criar ambiente virtual**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. **Configurar .env**:
   ```powershell
   cp .env.example .env
   # Editar .env e adicionar ANTHROPIC_API_KEY (necessário apenas na Fase 6)
   ```

4. **Implementar módulos**:
   - `src/pdf_splitter/ingest.py` - extrair páginas e texto nativo
   - `src/pdf_splitter/preprocess.py` - melhorar imagens para OCR
   - `src/pdf_splitter/ocr.py` - executar Tesseract

5. **Testar Fase 1**:
   ```python
   # Criar script de teste simples
   from src.pdf_splitter.ingest import ingest_pdf
   from src.pdf_splitter.ocr import batch_ocr
   
   pages = ingest_pdf("data/input/seu_pdf.pdf", "data/output/images")
   pages_with_ocr = batch_ocr(pages)
   
   # Verificar que texto foi extraído
   for page in pages_with_ocr[:3]:
       print(f"Página {page.page_number}:")
       print(page.ocr_text or page.native_text)
       print("-" * 60)
   ```

## Dependências Instaladas

Execute após criar o ambiente virtual:

```powershell
pip install -r requirements.txt
```

Bibliotecas incluídas:
- `pypdf` - manipulação de PDF
- `pdf2image` - conversão para imagem
- `pytesseract` - OCR
- `Pillow` + `opencv-python-headless` - processamento de imagem
- `anthropic` - API Claude (Fase 6)
- `pydantic` + `pydantic-settings` - validação de dados
- `pandas` + `openpyxl` - relatórios
- `streamlit` - interface web (Fase 8)
- `pytest` - testes

## Arquivos Especiais

### `.cursorrules`
Contém as convenções do projeto para o assistente de IA. Já configurado.

### `.env.example`
Template de configuração. Copie para `.env` e preencha seus valores.

### `schemas.py`
Define os contratos de dados entre módulos. **NÃO ALTERAR** sem revisar todos os módulos que usam.

## Comandos Úteis

```powershell
# Ativar ambiente virtual
.\venv\Scripts\Activate.ps1

# Executar CLI (quando implementado)
python cli.py data/input/exemplo.pdf data/output/resultado/

# Executar testes
pytest tests/ -v

# Executar interface web (Fase 8)
streamlit run app_streamlit.py

# Verificar tipos (opcional)
mypy src/
```

## Notas Importantes

1. **Implementar uma fase por vez** - Não pular para frente
2. **Testar cada módulo isoladamente** antes de integrar
3. **Não commitar dados reais** - `data/input/` e `data/output/` estão no `.gitignore`
4. **Seguir os schemas** definidos em `schemas.py`
5. **Normalizar texto** antes de aplicar regras (acentos, maiúsculas)
6. **Nunca perder páginas** - toda falha deve marcar `needs_review=True`

## Critérios de Aceite por Fase

Ver `docs/06_roadmap_fases.md` para critérios detalhados de cada fase.

**Fase 1**: Extrair texto de todas as páginas sem erro  
**Fase 2**: 70%+ das páginas classificadas com confiança alta  
**Fase 3**: Número de grupos próximo do esperado (~34 para o PDF de 46 páginas)  
**Fase 4**: Soma de páginas dos PDFs gerados == total do PDF original  
**Fase 5**: Rodar comando CLI ponta a ponta com sucesso  
**Fase 6**: Páginas não classificadas recebem classificação via LLM  
**Fase 7**: Testes automatizados passando  
**Fase 8**: Interface web funcional (opcional)  

## Precisa de Ajuda?

Consulte a documentação em `docs/`:
- **01_arquitetura.md** - visão geral do sistema
- **04_especificacao_modulos.md** - contratos detalhados
- **05_regras_classificacao.md** - tipos de documento suportados
- **07_prompts_llm.md** - prompts para API Anthropic

---

**Última atualização**: Fase 0 completa - 14/08/2026
