"""
Configurações globais do sistema.

Carrega variáveis de ambiente e define constantes usadas pelo pipeline.
"""

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
    ocr_language: str = "por"
    ocr_min_confidence: int = 60
    # 180 DPI é bem mais rápido que 300, com qualidade suficiente para comprovantes
    ocr_dpi: int = 180

    # Pastas padrão
    default_input_dir: Path = Path("data/input")
    default_output_dir: Path = Path("data/output")

    # Pré-processamento pesado (OpenCV) — desligado por padrão; deixa o OCR lento
    enable_preprocessing: bool = False

    # Texto nativo mínimo para considerar OCR desnecessário
    min_native_text_length: int = 50


settings = Settings()
