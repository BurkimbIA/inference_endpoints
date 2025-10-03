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
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY test_input.json ./test_input.json

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app

USER app

# Set environment variable for extended cold start timeout
ENV RUNPOD_INIT_TIMEOUT=800

EXPOSE 8000

CMD ["python", "-u", "src/handler.py", "--rp_serve_api", "--rp_api_host", "0.0.0.0"]