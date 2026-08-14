"""
Módulo de agrupamento de páginas em documentos.

Responsabilidade:
- Analisar lista de ClassificationResult (na ordem das páginas)
- Decidir quais páginas consecutivas formam um único documento
- Retornar lista de DocumentGroup

Entrada: list[ClassificationResult] (ordenados por page_number)
Saída: list[DocumentGroup]

Regras de agrupamento (em ordem de prioridade):
1. Mesmo doc_type E mesmo supplier em páginas consecutivas → mesmo grupo
2. Texto contém padrão de continuação ("página 2 de 2", "2/2") → mesmo grupo
3. Caso contrário → novo grupo
"""

import re
from .schemas import ClassificationResult, DocumentGroup
from .config import settings


def group_pages(classifications: list[ClassificationResult]) -> list[DocumentGroup]:
    """
    Agrupa páginas consecutivas em documentos.
    
    Args:
        classifications: Lista de ClassificationResult ordenados por page_number
        
    Returns:
        Lista de DocumentGroup representando documentos identificados
        
    Lógica de agrupamento:
    - Páginas consecutivas com mesmo doc_type E mesmo supplier → mesmo grupo
    - Padrões de continuação detectados → mesmo grupo
    - Confiança baixa em qualquer página do grupo → needs_review=True
    
    Validações:
    - Toda página deve pertencer a exatamente um grupo
    - Grupos devem ser consecutivos (start_page <= end_page)
    - Não pode haver páginas faltando entre grupos
    """
    if not classifications:
        return []
    
    # Ordenar por page_number (garantir ordem correta)
    classifications = sorted(classifications, key=lambda c: c.page_number)
    
    groups = []
    current_group = None
    
    for i, classification in enumerate(classifications):
        is_low_confidence = classification.confidence < settings.classification_confidence_threshold
        
        # Determinar se deve iniciar novo grupo ou continuar o atual
        if current_group is None:
            # Primeiro grupo
            current_group = {
                'doc_type': classification.doc_type,
                'supplier': classification.supplier,
                'start_page': classification.page_number,
                'end_page': classification.page_number,
                'needs_review': is_low_confidence,
            }
        else:
            # Verificar se deve agrupar com o anterior
            previous = classifications[i - 1]
            
            if should_group(classification, previous):
                # Continuar grupo atual
                current_group['end_page'] = classification.page_number
                if is_low_confidence:
                    current_group['needs_review'] = True
            else:
                # Finalizar grupo atual e iniciar novo
                groups.append(DocumentGroup(**current_group))
                current_group = {
                    'doc_type': classification.doc_type,
                    'supplier': classification.supplier,
                    'start_page': classification.page_number,
                    'end_page': classification.page_number,
                    'needs_review': is_low_confidence,
                }
    
    # Adicionar último grupo
    if current_group:
        groups.append(DocumentGroup(**current_group))
    
    print(f"\nAgrupamento: {len(classifications)} paginas -> {len(groups)} documentos")
    
    return groups


def detect_continuation_pattern(text: str) -> bool:
    """
    Detecta se o texto indica continuação de documento.
    
    Padrões comuns em documentos brasileiros:
    - "1 de 2", "2 de 2", "página 1/2"
    - "continuação"
    - "2/2", "3/3" etc isolado
    
    Returns:
        True se detectar padrão de continuação
    """
    if not text:
        return False
    
    text_lower = text.lower()
    
    # Padrões de continuação
    patterns = [
        r'\d+\s*de\s*\d+',           # "1 de 2", "2 de 2"
        r'página\s*\d+/\d+',         # "página 1/2"
        r'\d+/\d+',                  # "2/2" isolado
        r'continuação',              # palavra "continuação"
        r'continuacao',              # sem acento (OCR pode errar)
        r'folha\s*\d+\s*de\s*\d+',  # "folha 2 de 3"
    ]
    
    for pattern in patterns:
        if re.search(pattern, text_lower):
            return True
    
    return False


def should_group(
    current: ClassificationResult,
    previous: ClassificationResult,
) -> bool:
    """
    Decide se duas páginas consecutivas devem ser agrupadas.
    
    Args:
        current: Classificação da página atual
        previous: Classificação da página anterior
        
    Returns:
        True se devem ser agrupadas no mesmo documento
    """
    # Regra 1: Mesmo doc_type E mesmo supplier
    if (current.doc_type == previous.doc_type and 
        current.supplier == previous.supplier and
        current.doc_type != "desconhecido"):
        return True
    
    # Regra 2: Padrão de continuação detectado
    # (não podemos acessar o texto aqui, mas isso seria feito na classificação)
    # Por enquanto, usamos apenas tipo e fornecedor
    
    # Regra 3: Mesmo tipo e ambos sem fornecedor identificado
    # (comum em documentos simples como planilhas)
    if (current.doc_type == previous.doc_type and
        current.supplier is None and
        previous.supplier is None and
        current.doc_type != "desconhecido"):
        # Mais cauteloso: só agrupar se confiança razoável
        if current.confidence >= 0.7 and previous.confidence >= 0.7:
            return True
    
    return False
