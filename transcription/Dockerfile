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
    && rm -rf /var/lib/apt/lists/*

# Initialize git lfs
RUN git lfs install

WORKDIR /app

# Install Python dependencies first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install  -r requirements.txt
    # pip install --no-cache-dir -r requirements.txt

# Clone and cache the model during build (BEST PRACTICE for RunPod)
# This embeds the model in the Docker image for fastest loading
ARG HF_TOKEN
RUN git clone https://burkimbia:${HF_TOKEN}@huggingface.co/burkimbia/BIA-WHISPER-LARGE-SACHI_V2 /app/models/BIA-WHISPER-LARGE-SACHI_V2 && \
    cd /app/models/BIA-WHISPER-LARGE-SACHI_V2 && \
    git lfs pull && \
    # Remove git history to reduce image size
    rm -rf /app/models/BIA-WHISPER-LARGE-SACHI_V2/.git

# Copy application code
COPY src/ ./src/
COPY test_input.json ./test_input.json

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app

USER app

# Set environment variable for extended cold start timeout (if needed)
# Uncomment and adjust if your model loading takes >7 minutes
# ENV RUNPOD_INIT_TIMEOUT=800

EXPOSE 8000

CMD ["python", "-u", "src/handler.py", "--rp_serve_api", "--rp_api_host", "0.0.0.0"]