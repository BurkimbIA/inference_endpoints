# syntax=docker/dockerfile:1
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
COPY test_input.json ./test_input.json

# Create cache directory
RUN mkdir -p /app/cache

# Essential environment variables
ARG HF_TOKEN
ENV HF_TOKEN=${HF_TOKEN}
ENV TRANSFORMERS_CACHE=/app/cache
ENV HF_HOME=/app/cache
ENV TORCH_HOME=/app/cache

# Preload the model BEFORE switching to non-root user
RUN --mount=type=cache,target=/app/cache,uid=0,gid=0 python -c "from transformers import AutoModelForSeq2SeqLM; \
    import os; \
    AutoModelForSeq2SeqLM.from_pretrained('burkimbia/BIA-NLLB-600M-5E', token=os.environ['HF_TOKEN'])"

RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app

USER app

EXPOSE 8000
# CMD ["python", "-u", "src/handler.py", "--rp_serve_api"]
CMD ["python", "-u", "src/handler.py", "--rp_serve_api", "--rp_api_host", "0.0.0.0"]
