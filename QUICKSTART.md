# 🚀 Quick Start Guide: Docker Images & Endpoint Management

## 🐳 **ONE IMAGE, MULTIPLE ENDPOINTS**

You only need **ONE Docker image** that contains both models! The behavior changes based on environment variables:

```bash
# Build ONE image with BOTH models
./scripts/deploy.sh build burkimbia/translation-models latest

# This single image can create 3 different endpoints:
# 1. Mistral-only (MISTRAL_MODEL_ID set, NLLB_MODEL_NAME empty)
# 2. NLLB-only (NLLB_MODEL_NAME set, MISTRAL_MODEL_ID empty)  
# 3. Unified (BOTH set)
```

## 🎯 **ENDPOINT MANAGEMENT COMMANDS**

### **List All Endpoints & Costs**
```bash
# See all your endpoints and current costs
./scripts/deploy.sh list

# Show detailed cost breakdown
./scripts/deploy.sh costs
```

### **Deploy Individual Endpoints**
```bash
# Deploy NLLB only (cheapest - 1 model)
./scripts/deploy.sh deploy nllb_endpoint staging burkimbia/translation-models:latest

# Deploy Mistral only 
./scripts/deploy.sh deploy mistral_endpoint staging burkimbia/translation-models:latest

# Deploy both models in one endpoint (recommended)
./scripts/deploy.sh deploy unified_endpoint staging burkimbia/translation-models:latest
```

### **Destroy Endpoints (Stop Costs)**
```bash
# Destroy specific endpoint
./scripts/deploy.sh destroy burkimbia-nllb-translation

# 🚨 EMERGENCY: Destroy ALL endpoints (stops all costs immediately)
./scripts/deploy.sh emergency-stop
```

### **Redeploy Endpoints (Update)**
```bash
# Destroy and redeploy with new image
./scripts/deploy.sh redeploy unified_endpoint production burkimbia/translation-models:v2.0.0
```

## 💰 **COST CONTROL STRATEGY**

### **Budget-Friendly Approach:**
1. **Use unified_endpoint** - Both models in 1 worker = $0.50/hour max
2. **Deploy to staging first** - Test before production
3. **Destroy when not needed** - `./scripts/deploy.sh destroy endpoint-name`
4. **Monitor costs daily** - `./scripts/deploy.sh costs`

### **Development Workflow:**
```bash
# 1. Setup environment
./scripts/deploy.sh setup
export RUNPOD_API_KEY="your-key"
export HF_TOKEN="your-token"

# 2. Build and deploy to staging
./scripts/deploy.sh full-deploy unified_endpoint burkimbia/translation-models:dev

# 3. Test the endpoint
./scripts/deploy.sh test https://api.runpod.ai/v2/YOUR-ENDPOINT-ID/runsync

# 4. When satisfied, deploy to production
./scripts/deploy.sh deploy unified_endpoint production burkimbia/translation-models:v1.0.0

# 5. Destroy staging to save money
./scripts/deploy.sh destroy burkimbia-unified-translation-staging
```

## 🔧 **Environment Variables Control Model Loading**

```json
{
  "mistral_endpoint": {
    "env": {
      "MISTRAL_MODEL_ID": "your-mistral-model",  // ✅ Load Mistral
      "NLLB_MODEL_NAME": ""                      // ❌ Skip NLLB
    }
  },
  "nllb_endpoint": {
    "env": {
      "MISTRAL_MODEL_ID": "",                    // ❌ Skip Mistral
      "NLLB_MODEL_NAME": "V0.5(NLLB)"           // ✅ Load NLLB
    }
  },
  "unified_endpoint": {
    "env": {
      "MISTRAL_MODEL_ID": "your-mistral-model",  // ✅ Load both
      "NLLB_MODEL_NAME": "V0.5(NLLB)"           // ✅ Load both
    }
  }
}
```

## 📊 **Cost Examples**

| Scenario | Cost/Hour | Monthly (8h/day) |
|----------|-----------|------------------|
| No endpoints running | $0.00 | $0.00 |
| 1 NLLB endpoint | $0.50 | $120.00 |
| 1 Mistral endpoint | $0.50 | $120.00 |
| 1 Unified endpoint | $0.50 | $120.00 |
| All 3 endpoints | $1.50 | $360.00 |

## 🎯 **RECOMMENDATION FOR STUDENTS**

```bash
# 1. Use ONLY the unified endpoint (both models, one cost)
./scripts/deploy.sh deploy unified_endpoint staging burkimbia/translation-models:latest

# 2. Monitor costs regularly
./scripts/deploy.sh costs

# 3. Destroy when not actively developing
./scripts/deploy.sh destroy burkimbia-unified-translation

# 4. Emergency cost control
./scripts/deploy.sh emergency-stop
```

**Perfect for your budget! 🎓💚**