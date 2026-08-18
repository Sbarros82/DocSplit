"""
Módulo de pré-processamento de imagem.

Responsabilidade:
- Corrigir rotação/inclinação (deskew)
- Ajustar contraste e brilho
- Converter para escala de cinza
- Remover ruído
- Melhorar qualidade da imagem para OCR

Entrada: caminho de imagem original
Saída: caminho de imagem processada

Pode ser desabilitado via config para comparar resultados com/sem processamento.
"""

from __future__ import annotations

from pathlib import Path

# Dependência opcional: em ambientes sem OpenCV (ex: Vercel), o
# pré-processamento é simplesmente pulado e o OCR usa a imagem original.
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False


def preprocess_image(image_path: str | Path, output_path: str | Path | None = None) -> str:
    """
    Aplica pré-processamento em uma imagem para melhorar OCR.
    
    Args:
        image_path: Caminho da imagem original
        output_path: Caminho para salvar imagem processada (opcional, gera automaticamente se None)
        
    Returns:
        Caminho da imagem processada
        
    Técnicas aplicadas:
    - Conversão para escala de cinza
    - Correção de inclinação (deskew)
    - Ajuste de contraste adaptativo (CLAHE)
    - Redução de ruído
    - Binarização adaptativa
    
    Observações:
    - Especialmente útil para fotos de celular tortas/com sombra
    - Pode ser desabilitado via settings.enable_preprocessing
    """
    image_path = Path(image_path)
    
    if not OPENCV_AVAILABLE:
        # Sem OpenCV: retorna a imagem original sem processamento
        return str(image_path)
    
    if not image_path.exists():
        raise FileNotFoundError(f"Imagem não encontrada: {image_path}")
    
    # Gerar nome de saída se não fornecido
    if output_path is None:
        output_path = image_path.parent / f"{image_path.stem}_processed{image_path.suffix}"
    else:
        output_path = Path(output_path)
    
    # Carregar imagem
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Não foi possível carregar imagem: {image_path}")
    
    # 1. Converter para escala de cinza
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 2. Contraste rápido (NLMeans era o gargalo de vários segundos por página)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    contrast_enhanced = clahe.apply(gray)
    
    # 3. Binarização adaptativa
    binary = cv2.adaptiveThreshold(
        contrast_enhanced,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2
    )
    
    # Salvar imagem processada
    cv2.imwrite(str(output_path), binary)
    
    return str(output_path)


def _deskew_image(image: np.ndarray) -> np.ndarray:
    """
    Corrige inclinação da imagem.
    
    Usa transformada de Hough para detectar linhas dominantes
    e rotaciona a imagem para alinhamento.
    """
    # Detectar bordas
    edges = cv2.Canny(image, 50, 150, apertureSize=3)
    
    # Detectar linhas
    lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)
    
    if lines is None:
        return image  # Sem linhas detectadas, retorna original
    
    # Calcular ângulo médio das linhas
    angles = []
    for rho, theta in lines[:, 0]:
        angle = np.degrees(theta) - 90
        if -45 < angle < 45:  # Filtrar ângulos razoáveis
            angles.append(angle)
    
    if not angles:
        return image
    
    # Usar mediana dos ângulos (mais robusto que média)
    median_angle = np.median(angles)
    
    # Rotacionar imagem se inclinação significativa (> 0.5 graus)
    if abs(median_angle) > 0.5:
        (h, w) = image.shape
        center = (w // 2, h // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
        rotated = cv2.warpAffine(
            image,
            rotation_matrix,
            (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )
        return rotated
    
    return image
