# Translation Service

This service provides French ↔ Mooré translation using two different models:

## Models

### NLLB (Neural Machine Translation)
- **Model**: `burkimbia/BIA-NLLB-600M-5E`
- **Location**: Pre-loaded in Docker image at `/app/models/BIA-NLLB-600M-5E`
- **Use case**: Production-ready neural machine translation

### Mistral (Instruction-tuned)
- **Model**: `burkimbia/BIA-MISTRAL-7B-SACHI`
- **Location**: Loaded from Hugging Face at runtime
- **Use case**: Advanced context-aware translation

## Building the Docker Image

```bash
cd translation/
docker build --build-arg HF_TOKEN=$HF_TOKEN -t burkimbia/translation-service .
```

## Running the Service

```bash
docker run -p 8000:8000 -e HF_TOKEN=$HF_TOKEN burkimbia/translation-service
```

## API Usage

The service exposes a REST API for translation requests.