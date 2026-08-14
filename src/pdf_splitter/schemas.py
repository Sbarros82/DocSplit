"""
Modelos de dados compartilhados (Pydantic) para o pipeline.

Define os contratos de entrada/saída entre os módulos do sistema.
"""

from typing import Literal
from pydantic import BaseModel, Field


class Page(BaseModel):
    """Representa uma página extraída do PDF original."""
    
    page_number: int = Field(..., description="Número da página (1-indexed)")
    native_text: str | None = Field(None, description="Texto extraído nativamente do PDF")
    ocr_text: str | None = Field(None, description="Texto obtido via OCR")
    image_path: str | None = Field(None, description="Caminho da imagem renderizada da página")


class ClassificationResult(BaseModel):
    """Resultado da classificação de uma página."""
    
    page_number: int = Field(..., description="Número da página classificada")
    doc_type: str = Field(..., description="Tipo de documento identificado (ex: 'viasat_fatura', 'pix_comprovante')")
    supplier: str | None = Field(None, description="Nome do fornecedor/beneficiário identificado")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confiança da classificação (0.0 a 1.0)")
    source: Literal["rule", "llm"] = Field(..., description="Fonte da classificação: regra ou LLM")
    matched_pattern: str | None = Field(None, description="Qual regra/padrão bateu (para depuração)")


class DocumentGroup(BaseModel):
    """Grupo de páginas consecutivas que formam um documento."""
    
    doc_type: str = Field(..., description="Tipo de documento do grupo")
    supplier: str | None = Field(None, description="Fornecedor/beneficiário do documento")
    start_page: int = Field(..., description="Primeira página do grupo (1-indexed)")
    end_page: int = Field(..., description="Última página do grupo (1-indexed, inclusive)")
    needs_review: bool = Field(False, description="True se qualquer página do grupo tem baixa confiança")


class ExportedFile(BaseModel):
    """Representa um arquivo PDF exportado."""
    
    filename: str = Field(..., description="Nome do arquivo gerado")
    doc_type: str = Field(..., description="Tipo de documento")
    supplier: str | None = Field(None, description="Fornecedor/beneficiário")
    start_page: int = Field(..., description="Primeira página no PDF original")
    end_page: int = Field(..., description="Última página no PDF original")
    output_path: str = Field(..., description="Caminho completo do arquivo gerado")
    needs_review: bool = Field(False, description="True se o documento precisa de revisão manual")
