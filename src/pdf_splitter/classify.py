"""
Módulo de classificação de páginas.

Responsabilidade:
- Para cada página, tentar classificação por regras primeiro
- Se confiança < limiar, usar LLM como fallback
- Retornar ClassificationResult para cada página
- Cachear resultados por hash de texto (evitar reprocessamento)

Entrada: list[Page]
Saída: list[ClassificationResult]
"""

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Optional
from .schemas import Page, ClassificationResult
from .config import settings
from . import rules


def _default_cache_path() -> Path:
    """
    Caminho do cache de classificação.
    
    Em ambientes serverless (ex: Vercel) o diretório de trabalho é somente
    leitura, então o cache vai para o diretório temporário do sistema.
    """
    custom = os.environ.get("PDF_SPLITTER_CACHE_FILE")
    if custom:
        return Path(custom)
    if os.environ.get("VERCEL"):
        return Path(tempfile.gettempdir()) / "pdf_splitter_classification_cache.json"
    return Path(".classification_cache.json")


# Cache simples em arquivo JSON (evita chamar LLM para mesmo texto)
CACHE_FILE = _default_cache_path()


def classify_pages(pages: list[Page], use_llm_fallback: bool = False) -> list[ClassificationResult]:
    """
    Classifica uma lista de páginas usando regras + LLM fallback.
    
    Args:
        pages: Lista de objetos Page com texto extraído (native_text ou ocr_text)
        use_llm_fallback: Se True, usa LLM para páginas não classificadas (Fase 6)
        
    Returns:
        Lista de ClassificationResult, uma por página, na mesma ordem
        
    Lógica:
    1. Para cada página, obter o texto (ocr_text ou native_text)
    2. Calcular hash do texto e verificar cache
    3. Se não estiver no cache:
       a. Tentar rules.apply_rules()
       b. Se confidence < settings.classification_confidence_threshold:
          - Chamar llm_classify.classify_page() (fallback) [Fase 6]
    4. Adicionar resultado ao cache
    5. Retornar classificação
    
    Cache:
    - Armazenado em arquivo JSON local
    - Key: hash SHA256 do texto normalizado
    - Value: ClassificationResult serializado
    """
    cache = load_cache()
    classifications = []
    total = len(pages)
    classified_by_rules = 0
    low_confidence = 0
    
    for i, page in enumerate(pages, start=1):
        text = get_page_text(page)
        
        # Calcular hash para cache
        text_hash = compute_text_hash(text)
        
        # Verificar cache
        if text_hash in cache:
            result_data = cache[text_hash]
            result = ClassificationResult(**result_data)
            result.page_number = page.page_number  # Atualizar número da página
            if result.confidence >= settings.classification_confidence_threshold:
                classified_by_rules += 1
            else:
                low_confidence += 1
            classifications.append(result)
            continue
        
        # Tentar classificação por regras
        result = rules.apply_rules(text, page_number=page.page_number)
        
        if result and result.confidence >= settings.classification_confidence_threshold:
            # Classificação por regra com alta confiança
            classified_by_rules += 1
        elif use_llm_fallback:
            # TODO: Fase 6 - fallback para LLM
            # from . import llm_classify
            # result = llm_classify.classify_page(
            #     text,
            #     page.page_number,
            #     previous_doc_type=classifications[-1].doc_type if classifications else None,
            #     previous_supplier=classifications[-1].supplier if classifications else None,
            # )
            # Placeholder para Fase 2 (sem LLM ainda)
            result = ClassificationResult(
                page_number=page.page_number,
                doc_type="desconhecido",
                supplier=None,
                confidence=0.0,
                source="rule",
                matched_pattern=None,
            )
            low_confidence += 1
        else:
            # Sem fallback de LLM, marcar como não classificado
            result = ClassificationResult(
                page_number=page.page_number,
                doc_type="desconhecido",
                supplier=None,
                confidence=0.0 if not result else result.confidence,
                source="rule" if result else "rule",
                matched_pattern=result.matched_pattern if result else None,
            )
            low_confidence += 1
        
        # Adicionar ao cache
        cache[text_hash] = result.model_dump()
        classifications.append(result)
        
        # Progresso
        if i % 10 == 0 or i == total:
            print(f"Classificação: {i}/{total} páginas processadas")
    
    # Salvar cache
    save_cache(cache)
    
    # Estatísticas
    print(f"\nEstatísticas de classificação:")
    print(f"  - Classificadas por regras: {classified_by_rules}/{total} ({classified_by_rules/total*100:.1f}%)")
    print(f"  - Baixa confiança/desconhecidas: {low_confidence}/{total}")
    
    return classifications


def get_page_text(page: Page) -> str:
    """
    Obtém o melhor texto disponível de uma página.
    
    Prioridade: ocr_text > native_text > string vazia
    """
    if page.ocr_text:
        return page.ocr_text
    if page.native_text:
        return page.native_text
    return ""


def load_cache() -> dict:
    """Carrega cache de classificações do disco."""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            # Cache corrompido, ignorar
            return {}
    return {}


def save_cache(cache: dict) -> None:
    """Salva cache de classificações no disco."""
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Aviso: Não foi possível salvar cache: {e}")


def compute_text_hash(text: str) -> str:
    """Calcula hash SHA256 do texto normalizado."""
    normalized = rules.normalize_text(text)
    return hashlib.sha256(normalized.encode()).hexdigest()
