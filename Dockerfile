FROM pytorch/pytorch:2.2.1-cuda12.1-cudnn8-runtime


# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    git \
    wget \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/bin/python3 /usr/bin/python

WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY requirements.txt .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

ENV TRANSFORMERS_CACHE=/app/cache
ENV HF_HOME=/app/cache
ENV TORCH_HOME=/app/cache

RUN mkdir -p /app/cache

HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
  CMD python -c "from src.handler import health_check; print(health_check())" || exit 1

EXPOSE 8000

CMD ["python", "-u", "src/handler.py"]