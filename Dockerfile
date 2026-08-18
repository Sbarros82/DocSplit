# Fly.io Dockerfile para DocSplit com OCR

FROM python:3.11-slim

# Instalar dependências do sistema (Tesseract + Poppler)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    poppler-utils \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório de trabalho
WORKDIR /app

# Copiar requirements
COPY requirements-railway.txt requirements.txt

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Expor porta
EXPOSE 8080

# Comando de inicialização
CMD ["uvicorn", "api.index:app", "--host", "0.0.0.0", "--port", "8080"]
