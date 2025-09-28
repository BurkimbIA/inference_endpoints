# BURKIMBIA Translation Models - RunPod Serverless Deployment

Student-Budget Friendly: Optimized for NVIDIA T4 GPUs ($0.5/hour) to keep costs low while maintaining excellent performance.

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

```json
{
  "text": "Bonjour le monde",
  "model_type": "nllb",
  "src_lang": "fr_Latn", 
  "tgt_lang": "moor_Latn"
}
```

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

## Monitoring and Health Checks

The system includes comprehensive monitoring:

- Health Checks: Model loading status, system resources, environment validation
- Performance Metrics: Request latencies, success rates, system utilization
- Error Tracking: Detailed error logging and categorization
- Resource Monitoring: GPU memory, CPU, disk usage tracking

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

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Create an issue in the GitHub repository
- Contact the development team
- Check the troubleshooting guide above