# BURKIMBIA Translation Models - RunPod Serverless Deployment


A robust CI/CD pipeline for deploying French ↔ Mooré translation models (Mistral and NLLB) on RunPod serverless infrastructure.

## Architecture

- Mistral Model: Fine-tuned Mistral-Instruct model for French ↔ Mooré translation
- NLLB Model: Facebook's NLLB model adapted for multilingual translation including Mooré
- RunPod Serverless: GPU-accelerated serverless deployment platform
- GitHub Actions: Automated CI/CD pipeline for testing, building, and deployment

## Project Structure

```
├── src/
│   ├── handler.py         # RunPod serverless handler
│   ├── inferences.py      # Core translation model classes
│   └── monitoring.py      # Health checks and performance monitoring
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker container configuration
├── runpod-config.json    # RunPod deployment configurations
└── .github/workflows/    # GitHub Actions CI/CD pipelines
```

## Quick Start

### Prerequisites

1. Environment Variables:
   ```bash
   export RUNPOD_API_KEY="your-runpod-api-key"
   export HF_TOKEN="your-huggingface-token"
   ```

2. Required Tools:
   - Docker
   - Python 3.11+
   - Git

### Local Development Setup

1. Clone and setup:
   ```bash
   git clone <repository-url>
   cd inference-endpoints
   # Manual setup required - no scripts
   ```

2. Build Docker image:
   ```bash
   docker build -t burkimbia/translation-models:latest .
   ```

3. Deploy manually:
   ```bash
   # Manual deployment via RunPod console
   # Use the runpod-config.json for configuration
   ```

### Manual Deployment

```bash
# Build Docker image
docker build -t burkimbia/translation-models:v1.0.0 .

# Push to registry
docker push burkimbia/translation-models:v1.0.0

# Deploy via RunPod console using runpod-config.json
```

## Configuration

### Model endpoints

The system supports three deployment modes:

1. Mistral Only: Deploy only the Mistral translation model
2. NLLB Only: Deploy only the NLLB translation model  
3. Unified: Deploy both models in a single endpoint (recommended)

### RunPod configuration

Budget-Optimized for T4 GPUs:

```json
{
  "unified_endpoint": {
    "name": "burkimbia-unified-translation",
    "gpu_types": ["NVIDIA T4"],
    "min_gpus": 1,
    "max_gpus": 1,
    "gpu_memory": "16GB",
    "container_disk_size": "15GB",
    "volume_size": "8GB",
    "scaling": {
      "min_workers": 0,
      "max_workers": 1,
      "idle_timeout": 300
    }
  }
}
```

### Cost optimization features

- T4 GPUs Only: $0.5/hour (most budget-friendly)
- Conservative Scaling: Max 1-2 workers to control costs
- Smart Idle Timeout: 5 minutes to minimize idle charges
- Reduced Storage: Optimized disk and volume sizes
- Zero Minimum Workers: Pay only when processing requests

## CI/CD pipeline

### GitHub actions workflow

The pipeline includes:

1. Testing: Code linting, format checking, and basic import tests
2. Building: Multi-architecture Docker image builds with caching
3. Deployment: Automated deployment to staging/production environments
4. Testing: Comprehensive smoke tests post-deployment
5. Notification: Slack notifications for deployment status

### Environments

- Staging: Deployed on develop branch pushes
- Production: Deployed on main branch pushes or manual triggers

### Secrets configuration

Set the following secrets in your GitHub repository:

```
RUNPOD_API_KEY=your-runpod-api-key
HF_TOKEN=your-huggingface-token
DOCKER_USERNAME=your-docker-hub-username
DOCKER_PASSWORD=your-docker-hub-password
```

## API usage

### Translation request

**Basic request:**
```json
{
  "text": "Bonjour le monde",
  "model_type": "nllb",
  "src_lang": "fr_Latn", 
  "tgt_lang": "moor_Latn"
}
```

**With max_tokens parameter (recommended):**
```json
{
  "text": "Bonjour le monde",
  "model_type": "mistral",
  "src_lang": "fra_Latn",
  "tgt_lang": "moor_Latn",
  "max_tokens": 256
}
```

**NLLB with advanced parameters:**
```json
{
  "text": "Bonjour le monde",
  "model_type": "nllb",
  "src_lang": "fr_Latn",
  "tgt_lang": "moor_Latn",
  "max_tokens": 200,
  "num_beams": 3,
  "max_input_length": 512
}
```

### Parameters

#### Common Parameters (Both Models)

- **text** (required): Text to translate
- **model_type** (required): "mistral" or "nllb"
- **src_lang** (required): Source language code
- **tgt_lang** (required): Target language code
- **max_tokens** (optional): Maximum tokens to generate
  - **Mistral**: Default is 512 tokens
  - **NLLB**: If not specified, uses dynamic calculation (a + b * input_length)

#### NLLB-Specific Parameters

When `max_tokens` is not provided, NLLB uses these parameters for dynamic token calculation:

- **a** (optional): Base token count (default: 32)
- **b** (optional): Multiplier for input length (default: 3)  
- **max_input_length** (optional): Maximum input tokens (default: 1024)
- **num_beams** (optional): Number of beams for beam search (default: 5)

**Note:** If you specify `max_tokens`, the `a` and `b` parameters are ignored.

### Response

```json
{
  "translated_text": "Laafi boond-n",
  "model_type": "nllb",
  "src_lang": "fr_Latn",
  "tgt_lang": "moor_Latn",
  "processing_time_ms": 1250,
  "success": true
}
```

### Health check

```json
{
  "action": "health"
}
```

### Performance metrics

```json
{
  "action": "metrics"
}
```

### Usage Examples

#### 1. Quick Translation (Mistral)
```json
{
  "text": "Comment allez-vous?",
  "model_type": "mistral",
  "src_lang": "fra_Latn",
  "tgt_lang": "moor_Latn"
}
```

#### 2. Short Response (Both Models)
```json
{
  "text": "Oui",
  "model_type": "nllb",
  "src_lang": "fr_Latn",
  "tgt_lang": "moor_Latn",
  "max_tokens": 10
}
```

#### 3. Long Text Translation
```json
{
  "text": "Long paragraph to translate...",
  "model_type": "nllb",
  "src_lang": "fr_Latn",
  "tgt_lang": "moor_Latn",
  "max_tokens": 500,
  "max_input_length": 2048
}
```

#### 4. High Quality Translation (NLLB)
```json
{
  "text": "Technical documentation text",
  "model_type": "nllb",
  "src_lang": "en_Latn",
  "tgt_lang": "moor_Latn",
  "max_tokens": 300,
  "num_beams": 8
}
```



## Testing

### Manual Testing

```bash
# Test endpoint manually via RunPod console or API
# Use the API examples shown above
```

### Test Cases

The smoke tests include:
- Translation accuracy tests for both models
- Performance benchmarks
- Error handling validation  
- Health check verification
- Invalid input handling

## Supported Languages

### Mistral Model
- French (fra_Latn) ↔ Mooré (moor_Latn)

### NLLB Model
- French (fr_Latn) ↔ Mooré (moor_Latn)
- English (en_Latn) ↔ Mooré (moor_Latn)
- Additional languages supported by NLLB



## Contributing

1. Create a feature branch from develop
2. Make your changes
2. Run tests: Manual testing via RunPod console
4. Submit a pull request
5. CI pipeline will automatically test and validate

