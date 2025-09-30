FROM pytorch/pytorch:2.2.1-cuda12.1-cudnn8-runtime

RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY requirements.txt .

# Copier le fichier de test pour les tests locaux
COPY test_input.json ./test_input.json

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app

# Create cache directory BEFORE changing ownership
RUN mkdir -p /app/cache

# Change ownership of everything
RUN chown -R app:app /app

USER app

# Essential environment variables
ENV HF_TOKEN=REMOVED_TOKEN

# Cache directories
ENV TRANSFORMERS_CACHE=/app/cache
ENV HF_HOME=/app/cache
ENV TORCH_HOME=/app/cache

EXPOSE 8000

CMD ["python", "-u", "src/handler.py"]