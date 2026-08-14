# Guia de Início Rápido

**Separador Inteligente de Documentos PDF**

## 🚀 Começar em 5 Minutos

### Pré-requisitos
- Windows 10/11
- Python 3.11+
- Acesso administrativo para instalação

### Passo 1: Instalar Poppler e Tesseract

#### Poppler (para PDF)
1. Baixe: https://github.com/oschwartz10612/poppler-windows/releases/
2. Extraia para `C:\Program Files\poppler`
3. Adicione ao PATH: `C:\Program Files\poppler\Library\bin`

#### Tesseract OCR
1. Baixe: https://github.com/UB-Mannheim/tesseract/wiki
2. Execute o instalador
3. **IMPORTANTE**: Marque "Portuguese" durante a instalação

### Passo 2: Instalar Dependências Python

```powershell
# No diretório d:\Snap

# Criar ambiente virtual
python -m venv venv

# Ativar (se der erro, execute como admin: Set-ExecutionPolicy RemoteSigned)
.\venv\Scripts\Activate.ps1

# Instalar pacotes
pip install -r requirements.txt
```

### Passo 3: Testar Instalação

Crie um arquivo `test_instalacao.py`:

```python
# test_instalacao.py
print("Testando instalações...")

try:
    from pdf2image import convert_from_path
    print("✓ pdf2image OK")
except Exception as e:
    print(f"✗ pdf2image ERRO: {e}")

try:
    import pytesseract
    print("✓ pytesseract OK")
except Exception as e:
    print(f"✗ pytesseract ERRO: {e}")

try:
    from pypdf import PdfReader
    print("✓ pypdf OK")
except Exception as e:
    print(f"✗ pypdf ERRO: {e}")

print("\nSe todos estão OK, você está pronto! 🎉")
```

Execute:
```powershell
python test_instalacao.py
```

### Passo 4: Testar com PDF de Exemplo

```powershell
# Coloque um PDF em data/input/teste.pdf
# Pode ser qualquer PDF com documentos misturados

# Executar CLI
python cli.py data/input/teste.pdf data/output/resultado/
```

### Saída Esperada

```
data/output/resultado/
├── 01_tipo_documento_fornecedor.pdf
├── 02_tipo_documento_fornecedor.pdf
├── ...
├── index.xlsx                    # Planilha com índice
└── teste_separados.zip          # ZIP com todos os PDFs
```

## 📊 Exemplo de Uso Real

### Cenário: Separar Comprovantes Financeiros

**Entrada**: PDF de 46 páginas com boletos, PIX, notas fiscais misturados

```powershell
python cli.py data/input/comprovantes_julho.pdf data/output/julho/
```

**Resultado esperado**: ~34 documentos separados automaticamente

### O que o sistema faz:

1. ✅ Extrai cada página como imagem
2. ✅ Roda OCR em páginas escaneadas
3. ✅ Classifica tipo de cada página (PIX, boleto, NF-e, etc.)
4. ✅ Agrupa páginas do mesmo documento (ex: "1 de 2", "2 de 2")
5. ✅ Gera PDFs individuais com nomes descritivos
6. ✅ Cria planilha Excel com índice completo

## 🔍 Entendendo a Saída

### Arquivo: `01_pix_comprovante_maria_silva.pdf`
- `01` = ordem sequencial
- `pix_comprovante` = tipo de documento detectado
- `maria_silva` = beneficiário identificado

### Planilha `index.xlsx`
| Número | Arquivo | Tipo de Documento | Fornecedor | Páginas Originais |
|--------|---------|-------------------|------------|-------------------|
| 1 | 01_pix_comprovante_maria_silva.pdf | Comprovante PIX | Maria Silva | 5 |
| 2 | 02_viasat_fatura.pdf | Fatura Viasat | Viasat Brasil | 6-8 |
| ... | ... | ... | ... | ... |

## ⚙️ Opções da CLI

```powershell
# Básico
python cli.py entrada.pdf saida/

# Sem criar ZIP
python cli.py --no-zip entrada.pdf saida/

# Sem pré-processar imagens (mais rápido, mas OCR pode ser pior)
python cli.py --no-preprocess entrada.pdf saida/

# Modo verboso (mais detalhes)
python cli.py -v entrada.pdf saida/

# Ajuda
python cli.py --help
```

## 🐛 Solução de Problemas Comuns

### Erro: "Unable to get page count"
**Causa**: Poppler não está no PATH  
**Solução**: Adicione `C:\Program Files\poppler\Library\bin` ao PATH e reinicie PowerShell

### Erro: "TesseractNotFoundError"
**Causa**: Tesseract não instalado ou não está no PATH  
**Solução**: 
```python
# Adicione no início do seu script
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### Erro: "Failed loading language 'por'"
**Causa**: Idioma português não instalado no Tesseract  
**Solução**: Reinstale Tesseract marcando "Portuguese" na lista de idiomas

### OCR com muitos erros
**Causa**: Imagem de baixa qualidade, torta ou com sombras  
**Solução**: O pré-processamento está ativado por padrão e ajuda. Para melhor resultado, escaneie documentos com boa iluminação e planos.

### Documento não foi classificado corretamente
**Causa**: Tipo de documento não está nas regras  
**Solução**: 
1. Abra `src/pdf_splitter/rules.py`
2. Adicione nova regra com padrões do documento
3. Execute novamente

Exemplo:
```python
Rule(
    doc_type="novo_tipo_documento",
    patterns=["palavra-chave única", "outra palavra-chave"],
    confidence=0.9,
)
```

## 📈 Melhorando os Resultados

### 1. Adicionar Regras Específicas

Após processar alguns lotes, você notará padrões. Adicione-os em `rules.py`:

```python
Rule(
    doc_type="contrato_fornecedor_x",
    patterns=["razão social do fornecedor", "cnpj específico"],
    supplier_pattern=r"Fornecedor:\s*(.+?)(?:\n|$)",
    confidence=0.95,
)
```

### 2. Ajustar Limiar de Confiança

No arquivo `.env`:
```
CLASSIFICATION_CONFIDENCE_THRESHOLD=0.8  # Padrão
# Baixe para 0.7 se muitos documentos ficam sem classificar
# Suba para 0.9 se muitos falsos positivos
```

### 3. Revisar Documentos Manualmente

Documentos de baixa confiança são marcados no `index.xlsx`. Revise-os e adicione regras para os tipos novos.

## 🎯 Dicas de Produtividade

### Processar Múltiplos PDFs

```powershell
# Script PowerShell para processar pasta inteira
$pdfs = Get-ChildItem data/input/*.pdf
foreach ($pdf in $pdfs) {
    $output = "data/output/" + $pdf.BaseName
    python cli.py $pdf.FullName $output
}
```

### Organizar por Mês

```powershell
python cli.py comprovantes_janeiro.pdf data/output/2026/01_janeiro/
python cli.py comprovantes_fevereiro.pdf data/output/2026/02_fevereiro/
```

### Backup Automático

Configure para criar ZIP sempre:
```powershell
python cli.py entrada.pdf saida/  # ZIP criado por padrão
```

## 📞 Suporte

- **Documentação completa**: Ver pasta `docs/`
- **Status**: Ver `STATUS_IMPLEMENTACAO.md`
- **Setup detalhado**: Ver `SETUP_WINDOWS.md`

## ✅ Checklist Pós-Instalação

- [ ] Poppler instalado e no PATH
- [ ] Tesseract instalado com idioma português
- [ ] Ambiente virtual Python criado e ativado
- [ ] Pacotes Python instalados (`pip install -r requirements.txt`)
- [ ] `test_instalacao.py` executado com sucesso
- [ ] Primeiro PDF de teste processado com sucesso

**Pronto! Você está apto a processar documentos! 🚀**

---

Próximo passo: Processar seu primeiro lote real de documentos e ajustar regras conforme necessário.
