# BURKIMBIA Translation Models - RunPod Deployment

Deploy and destroy French ↔ Mooré translation endpoints (Mistral, NLLB, Unified) on RunPod using GitHub Actions.

## Usage

### 1. Configure secrets

- `RUNPOD_API_KEY`: Your RunPod API key
- `HF_TOKEN`: Your HuggingFace token
- `DOCKER_USERNAME`: Docker Hub username

### 2. Deploy an endpoint

Go to GitHub Actions > DEPLOY - RunPod Endpoints > Run workflow
Choose model: `mistral_endpoint`, `nllb_endpoint`, or `unified_endpoint`

### 3. Destroy an endpoint

Go to GitHub Actions > DESTROY - RunPod Endpoints > Run workflow
Choose model to destroy
Type `CONFIRM` to validate

## Configuration

Edit `runpod-config.json` to change endpoint names, model types, GPU, scaling, etc.

## API Example

Request:
```
{
  "text": "Bonjour le monde",
  "model_type": "nllb",
  "src_lang": "fr_Latn",
  "tgt_lang": "moor_Latn"
}
```


