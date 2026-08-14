# 👋 Bem-vindo ao Separador Inteligente de Documentos!

## 🎯 O que este projeto faz?

Transforma isto:
```
📄 comprovantes.pdf (46 páginas misturadas)
```

Nisto:
```
📁 pasta_organizada/
├── 01_pix_maria.pdf
├── 02_boleto_vivo.pdf
├── 03_nfe_mercado.pdf
├── ... (34 documentos)
└── index.xlsx
```

**Automaticamente!** ⚡

---

## 🚀 Por onde começar?

### Para USAR o sistema (recomendado):

1. 📖 Leia: **`INICIO_RAPIDO.md`** ← COMECE AQUI!
2. ⚙️ Siga: **`SETUP_WINDOWS.md`** para instalar dependências
3. ▶️ Execute: `python cli.py seu_arquivo.pdf saida/`
4. ✅ Pronto!

### Para ENTENDER o projeto:

1. 📊 Veja: **`RESUMO_PROJETO.md`** para visão geral
2. 🔄 Leia: **`FLUXO_SISTEMA.txt`** para entender o fluxo
3. 📈 Confira: **`STATUS_IMPLEMENTACAO.md`** para status detalhado

### Para DESENVOLVER/MODIFICAR:

1. 📚 Leia: **`README_DESENVOLVIMENTO.md`**
2. 📁 Explore: **`docs/`** para documentação técnica
3. 🔧 Edite: **`src/pdf_splitter/rules.py`** para adicionar tipos

---

## 📚 Guia de Documentos

| Arquivo | Para Quem? | Tempo | O que tem? |
|---------|-----------|-------|------------|
| **INICIO_RAPIDO.md** ⭐ | Usuários | 5 min | Setup e primeiro uso |
| **SETUP_WINDOWS.md** | Todos | 10 min | Instalar Poppler + Tesseract |
| **RESUMO_PROJETO.md** | Todos | 5 min | Visão completa |
| **FLUXO_SISTEMA.txt** | Técnicos | 3 min | Diagrama do fluxo |
| **STATUS_IMPLEMENTACAO.md** | Desenvolvedores | 10 min | Status e roadmap |
| **README_DESENVOLVIMENTO.md** | Desenvolvedores | 15 min | Guia de desenvolvimento |
| **docs/** | Desenvolvedores | 30 min | Specs técnicas |

---

## ⚡ Início Ultra-Rápido (já tem Python?)

```powershell
# 1. Instalar dependências (uma vez - ver SETUP_WINDOWS.md)
#    - Poppler: https://github.com/oschwartz10612/poppler-windows/releases/
#    - Tesseract: https://github.com/UB-Mannheim/tesseract/wiki

# 2. Criar ambiente Python
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. Testar instalação
python -c "from pdf2image import convert_from_path; import pytesseract; print('✓ OK')"

# 4. Processar seu PDF
python cli.py data/input/teste.pdf data/output/resultado/

# 5. Ver resultado em data/output/resultado/
```

---

## 🎓 O que você precisa saber?

### Nível Usuário (apenas usar):
- ✅ Copiar um PDF para `data/input/`
- ✅ Executar um comando no PowerShell
- ✅ Abrir Excel para ver o índice
- ✅ Isso é tudo!

### Nível Técnico (modificar/desenvolver):
- Python 3.11+ básico
- Entender estrutura de módulos
- Editar regras em `rules.py`
- Ler documentação em `docs/`

---

## 💡 Casos de Uso

### 1. Contabilidade de Empresa
**Antes**: Recebe PDF com 50 comprovantes misturados  
**Depois**: 50 arquivos separados e nomeados para contabilidade

### 2. Organização Pessoal
**Antes**: PDFs de banco com múltiplos comprovantes  
**Depois**: Um arquivo por transação, fácil de encontrar

### 3. Digitalização em Massa
**Antes**: Scanner cria 1 PDF com tudo  
**Depois**: Documentos separados automaticamente

---

## 🔥 Status do Projeto

```
✅ Fase 0: Setup                     COMPLETO
✅ Fase 1: Ingestão + OCR            COMPLETO
✅ Fase 2: Classificação             COMPLETO
✅ Fase 3: Agrupamento               COMPLETO
✅ Fase 4: Geração de Saída          COMPLETO
✅ Fase 5: Pipeline + CLI            COMPLETO
⏳ Fase 6: LLM Fallback              OPCIONAL
⏳ Fase 7: Testes                    ESTRUTURA PRONTA
⏳ Fase 8: Interface Web             OPCIONAL
```

**O sistema está FUNCIONAL e PRONTO PARA USO!** 🎉

---

## 🆘 Precisa de Ajuda?

### Erro na instalação?
→ Veja `SETUP_WINDOWS.md` seção "Problemas Comuns"

### Não classificou um documento?
→ Adicione regra em `src/pdf_splitter/rules.py`

### Quer entender o código?
→ Leia `docs/04_especificacao_modulos.md`

### Encontrou um bug?
→ Verifique `STATUS_IMPLEMENTACAO.md` para limitações conhecidas

---

## 🎯 Próximo Passo

**Abra agora**: [`INICIO_RAPIDO.md`](INICIO_RAPIDO.md)

Tempo até primeiro resultado: **~10 minutos** ⚡

---

## 📊 Estatísticas do Projeto

- 17 módulos Python implementados
- 64 funções e classes
- 12 tipos de documentos brasileiros
- 6 guias de documentação
- 100% das fases 1-5 completas

---

## 🌟 Características

- ✅ **Rápido**: 2-5 minutos para 50 páginas
- ✅ **Preciso**: Regras determinísticas + OCR robusto
- ✅ **Seguro**: Valida que nenhuma página se perde
- ✅ **Organizado**: Nomes padronizados + índice Excel
- ✅ **Extensível**: Fácil adicionar novos tipos
- ✅ **Documentado**: 6 guias + documentação técnica

---

**🚀 Vamos começar?**

Abra: **`INICIO_RAPIDO.md`**

---

*Desenvolvido em 14/08/2026 - v0.1.0*
