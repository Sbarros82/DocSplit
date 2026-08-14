# Configuração no Windows

## Passo 1: Instalar Python 3.11+

Baixe e instale de: https://www.python.org/downloads/

Marque a opção "Add Python to PATH" durante a instalação.

## Passo 2: Instalar Poppler (para pdf2image)

1. Baixe a versão mais recente de: https://github.com/oschwartz10612/poppler-windows/releases/
2. Extraia para `C:\Program Files\poppler` (ou outro local de sua preferência)
3. Adicione ao PATH do sistema:
   - Abra "Variáveis de Ambiente" (Painel de Controle → Sistema → Configurações avançadas)
   - Em "Variáveis do sistema", selecione `Path` e clique em "Editar"
   - Adicione: `C:\Program Files\poppler\Library\bin`
   - Clique OK

4. Teste no PowerShell:
   ```powershell
   pdftoppm -v
   ```
   Deve mostrar a versão do Poppler.

## Passo 3: Instalar Tesseract OCR

1. Baixe o instalador de: https://github.com/UB-Mannheim/tesseract/wiki
2. Execute o instalador
3. **IMPORTANTE**: Durante a instalação:
   - Marque "Additional language data"
   - Selecione "Portuguese" (por) na lista de idiomas
4. O instalador adiciona Tesseract ao PATH automaticamente
5. Teste no PowerShell:
   ```powershell
   tesseract --version
   ```

**Localização padrão**: `C:\Program Files\Tesseract-OCR\tesseract.exe`

Se precisar configurar manualmente o caminho no código:
```python
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

## Passo 4: Criar Ambiente Virtual

No diretório do projeto (`d:\Snap`):

```powershell
# Criar ambiente virtual
python -m venv venv

# Ativar
.\venv\Scripts\Activate.ps1

# Se houver erro de política de execução, execute como admin:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Depois ative novamente
.\venv\Scripts\Activate.ps1

# Seu prompt deve mostrar (venv) no início
```

## Passo 5: Instalar Dependências Python

```powershell
# Com o ambiente virtual ativado
pip install --upgrade pip
pip install -r requirements.txt
```

## Passo 6: Configurar .env

```powershell
# Copiar template
cp .env.example .env

# Editar .env com seu editor preferido
notepad .env
```

Preencha:
```
ANTHROPIC_API_KEY=sk-ant-seu-token-aqui
CLASSIFICATION_CONFIDENCE_THRESHOLD=0.8
OCR_LANGUAGE=por
```

A `ANTHROPIC_API_KEY` só é necessária na Fase 6 (fallback LLM).

## Passo 7: Verificar Instalação

```powershell
# Verificar Python
python --version

# Verificar poppler
pdftoppm -v

# Verificar Tesseract
tesseract --version
tesseract --list-langs  # Deve mostrar 'por' na lista

# Verificar pacotes Python
pip list
```

## Passo 8: Testar com PDF de Exemplo

Coloque um PDF em `data/input/teste.pdf` e crie um script de teste:

```python
# test_setup.py
from pdf2image import convert_from_path
import pytesseract
from PIL import Image

# Teste pdf2image
print("Testando pdf2image...")
images = convert_from_path('data/input/teste.pdf', first_page=1, last_page=1)
print(f"✓ Primeira página convertida: {images[0].size}")

# Teste Tesseract
print("\nTestando Tesseract OCR...")
text = pytesseract.image_to_string(images[0], lang='por')
print(f"✓ Texto extraído ({len(text)} caracteres)")
print("Primeiros 200 caracteres:")
print(text[:200])
```

Execute:
```powershell
python test_setup.py
```

## Problemas Comuns

### Erro: "Unable to get page count. Is poppler installed?"
- Verifique se o PATH está configurado corretamente
- Reinicie o PowerShell após adicionar ao PATH
- Teste: `pdftoppm -v`

### Erro: "TesseractNotFoundError"
- Verifique se Tesseract está instalado
- Configure o caminho manualmente no código (ver Passo 3)

### Erro: "Failed loading language 'por'"
- Reinstale Tesseract e marque idioma português na instalação
- Ou baixe manualmente: https://github.com/tesseract-ocr/tessdata
- Coloque `por.traineddata` em `C:\Program Files\Tesseract-OCR\tessdata\`

### Erro ao ativar venv: "execution of scripts is disabled"
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Pronto!

Agora você pode começar a implementar a Fase 1:
```powershell
python cli.py data/input/seu_pdf.pdf data/output/resultado/
```

Para desenvolvimento com o Cursor, o ambiente está configurado e pronto! 🚀
