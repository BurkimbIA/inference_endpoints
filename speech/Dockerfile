# syntax=docker/dockerfile:1
FROM pytorch/pytorch:2.2.1-cuda12.1-cudnn8-runtime

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    git \
    git-lfs \
    curl \
    ffmpeg \
    espeak-ng \
    espeak-ng-data \
    && rm -rf /var/lib/apt/lists/*

# Initialize git lfs
RUN git lfs install

WORKDIR /app

# Install Python dependencies first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install -r requirements.txt

# Clone and cache speech synthesis models during build
# TODO: Add specific TTS models (e.g., Coqui TTS, XTTS, Bark)
ARG HF_TOKEN
# RUN git clone https://burkimbia:${HF_TOKEN}@huggingface.co/burkimbia/YOUR-TTS-MODEL /app/models/YOUR-TTS-MODEL && \
#     cd /app/models/YOUR-TTS-MODEL && \
#     git lfs pull && \
#     rm -rf /app/models/YOUR-TTS-MODEL/.git

# Copy application code
COPY src/ ./src/

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app

USER app

EXPOSE 8000

CMD ["python", "-u", "src/handler.py", "--rp_serve_api", "--rp_api_host", "0.0.0.0"]