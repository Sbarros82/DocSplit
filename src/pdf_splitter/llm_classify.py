"""
Módulo de classificação via LLM (fallback).

Responsabilidade:
- Classificar páginas que as regras não conseguiram identificar
- Usar API Anthropic (Claude) com prompt específico
- Retornar ClassificationResult com source="llm"
- Tratar erros de API graciosamente (não quebrar pipeline)

Entrada: texto da página + contexto opcional (páginas vizinhas)
Saída: ClassificationResult

Só é chamado quando rules.apply_rules() retorna confidence baixa.
Ver prompts em docs/07_prompts_llm.md
"""

import json
from typing import Optional
from anthropic import Anthropic, APIError
from .schemas import ClassificationResult
from .config import settings


def classify_page(
    text: str,
    page_number: int,
    previous_doc_type: Optional[str] = None,
    previous_supplier: Optional[str] = None,
) -> ClassificationResult:
    """
    Classifica uma página usando Claude (Anthropic API).
    
    Args:
        text: Texto extraído da página
        page_number: Número da página (para rastreamento)
        previous_doc_type: Tipo de documento da página anterior (contexto)
        previous_supplier: Fornecedor da página anterior (contexto)
        
    Returns:
        ClassificationResult com source="llm"
        
    Em caso de erro de API:
    - Retorna doc_type="desconhecido", confidence=0.0, source="llm"
    - Não levanta exceção (pipeline continua, marca needs_review=True)
    
    Observações:
    - Usa prompt definido em docs/07_prompts_llm.md
    - Espera resposta JSON do modelo
    - Timeout configurável
    - Requer ANTHROPIC_API_KEY em .env
    """
    # TODO: implementar
    pass


def build_classification_prompt(
    text: str,
    page_number: int,
    previous_doc_type: Optional[str] = None,
    previous_supplier: Optional[str] = None,
) -> str:
    """
    Constrói o prompt de classificação para o LLM.
    
    Baseado em docs/07_prompts_llm.md
    """
    # TODO: implementar prompt completo
    pass


def parse_llm_response(response_text: str, page_number: int) -> ClassificationResult:
    """
    Faz parsing da resposta JSON do LLM.
    
    Em caso de JSON inválido ou formato inesperado:
    - Retorna classificação de baixa confiança
    - Marca para revisão manual
    """
    # TODO: implementar
    pass
