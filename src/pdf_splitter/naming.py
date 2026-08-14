"""
Módulo de geração de nomes de arquivo padronizados.

Responsabilidade:
- Gerar nome de arquivo único para cada DocumentGroup
- Formato: {ordem:02d}_{doc_type}_{supplier_slug}_{data}.pdf
- Garantir nomes únicos (sufixos _via2, _via3 se necessário)

Entrada: DocumentGroup + índice sequencial
Saída: string com nome de arquivo
"""

import re
import unicodedata
from collections import defaultdict
from .schemas import DocumentGroup


# Contador de nomes duplicados por sessão
_name_counters: dict[str, int] = defaultdict(int)


def generate_filename(
    group: DocumentGroup,
    sequence_number: int,
    reset_counters: bool = False,
) -> str:
    """
    Gera nome de arquivo padronizado para um grupo de documentos.
    
    Args:
        group: DocumentGroup a ser nomeado
        sequence_number: Número sequencial do documento no lote (1-indexed)
        reset_counters: Se True, reseta contadores de nomes duplicados
        
    Returns:
        Nome de arquivo no formato: {ordem:02d}_{doc_type}_{supplier}_{data}.pdf
        
    Exemplos:
    - "01_pix_comprovante_maria_silva.pdf"
    - "02_viasat_fatura_julho2025.pdf"
    - "15_nfe_supermercado_sao_jose_via2.pdf" (segunda via do mesmo fornecedor)
    
    Comportamento com duplicatas:
    - Se já houver documento com mesmo doc_type e supplier neste lote,
      adiciona sufixo _via2, _via3, etc.
    """
    global _name_counters
    
    if reset_counters:
        _name_counters.clear()
    
    # Componentes do nome
    parts = [f"{sequence_number:02d}"]
    
    # Tipo de documento
    doc_type_slug = slugify(group.doc_type)
    parts.append(doc_type_slug)
    
    # Fornecedor (se houver)
    if group.supplier:
        supplier_slug = slugify(group.supplier)
        # Limitar tamanho do slug do fornecedor
        if len(supplier_slug) > 40:
            supplier_slug = supplier_slug[:40]
        parts.append(supplier_slug)
    
    # Criar chave única para detectar duplicatas
    unique_key = f"{doc_type_slug}_{group.supplier or 'none'}"
    
    # Verificar duplicata e adicionar sufixo se necessário
    _name_counters[unique_key] += 1
    if _name_counters[unique_key] > 1:
        parts.append(f"via{_name_counters[unique_key]}")
    
    # Montar nome final
    filename = "_".join(parts) + ".pdf"
    
    return filename


def slugify(text: str) -> str:
    """
    Converte texto em slug válido para nome de arquivo.
    
    Transformações:
    - Lowercase
    - Remove acentos
    - Substitui espaços e caracteres especiais por underscore
    - Remove caracteres inválidos para filesystem
    - Colapsa múltiplos underscores
    
    Exemplos:
    - "João da Silva" → "joao_da_silva"
    - "Prefeitura de São José" → "prefeitura_de_sao_jose"
    - "Energia Elétrica - Conta" → "energia_eletrica_conta"
    """
    if not text:
        return "desconhecido"
    
    # Lowercase
    text = text.lower()
    
    # Remover acentos
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ASCII', 'ignore').decode('ASCII')
    
    # Substituir caracteres especiais por underscore
    text = re.sub(r'[^\w\s-]', '_', text)
    
    # Substituir espaços e hífens por underscore
    text = re.sub(r'[\s-]+', '_', text)
    
    # Colapsar múltiplos underscores
    text = re.sub(r'_+', '_', text)
    
    # Remover underscores do início e fim
    text = text.strip('_')
    
    return text if text else "desconhecido"


def reset_naming_counters() -> None:
    """Reseta contadores de nomes duplicados (usado entre lotes)."""
    global _name_counters
    _name_counters.clear()
