"""
Configurações globais do sistema.

Carrega variáveis de ambiente e define constantes usadas pelo pipeline.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações do sistema carregadas de variáveis de ambiente."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # API Anthropic (legado — o fallback ativo usa OpenRouter)
    anthropic_api_key: str = ""

    # OpenRouter (fallback de classificação)
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o-mini"
    
    # Limiar de confiança para classificação
    classification_confidence_threshold: float = 0.8
    
    # OCR
    ocr_language: str = "por"  # português
    ocr_min_confidence: int = 60  # confiança mínima do Tesseract
    
    # Pastas padrão
    default_input_dir: Path = Path("data/input")
    default_output_dir: Path = Path("data/output")
    
    # Pré-processamento de imagem
    enable_preprocessing: bool = True
    
    # Texto nativo mínimo para considerar OCR desnecessário
    min_native_text_length: int = 50


# Instância global de configuração
settings = Settings()
