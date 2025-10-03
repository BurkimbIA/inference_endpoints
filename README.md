# 🤖 AI Services Infrastructure - BurkimbIA

Une infrastructure complète de services IA pour la traduction, transcription et synthèse vocale en mooré et français.

## 🏗️ Architecture des Services

```
📦 AI Services Infrastructure
├── 🔤 translation/          # Service de traduction (NLLB + Mistral)
├── 🎙️  transcription/        # Service de transcription (Whisper)
├── 🔊 speech/               # Service de synthèse vocale (TTS)
└── 🚀 CI/CD Pipeline        # Déploiement automatisé
```

## 🐳 Services Disponibles

### 🔤 **Translation Service**
- **Modèles**: NLLB-600M + Mistral-7B-SACHI
- **Langues**: Français ↔ Mooré
- **Image**: `docker.io/username/translation-service:latest`

### 🎙️ **Transcription Service**
- **Modèle**: BIA-WHISPER-LARGE-SACHI_V2
- **Fonction**: Audio → Texte (mooré, français)
- **Image**: `docker.io/username/transcription-service:latest`

### 🔊 **Speech Service** *(En développement)*
- **Modèles**: Coqui TTS, XTTS
- **Fonction**: Texte → Audio (mooré, français)
- **Image**: `docker.io/username/speech-service:latest`

## 🚀 CI/CD Pipeline

### **Build Automatique**
```bash
# Build tous les services
gh workflow run build.yml --field service=all

# Build service spécifique
gh workflow run build.yml --field service=translation
gh workflow run build.yml --field service=transcription
gh workflow run build.yml --field service=speech
```

### **Déploiement RunPod**
```bash
# Déployer service de traduction
gh workflow run deploy.yml --field service=translation_endpoint

# Déployer service de transcription  
gh workflow run deploy.yml --field service=transcription_endpoint

# Déployer service de speech
gh workflow run deploy.yml --field service=speech_endpoint
```

## 🔧 Configuration des Services

### **Variables d'environnement requises**
```bash
HF_TOKEN=your_huggingface_token
RUNPOD_API_KEY=your_runpod_api_key
DOCKER_USERNAME=your_docker_username
DOCKER_PASSWORD=your_docker_password
```

### **GPU Configuration**
- **Translation**: NVIDIA A40 (3 workers max)
- **Transcription**: NVIDIA A40 (2 workers max) 
- **Speech**: NVIDIA A40 (2 workers max)

## 📊 Endpoints de Production

### **Translation API**
```json
POST https://api.runpod.ai/v1/{endpoint_id}/run
Content-Type: application/json

{
  "input": {
    "text": "Bonjour comment allez-vous?",
    "src_lang": "fra_Latn",
    "tgt_lang": "moor_Latn",
    "model": "nllb"
  }
}
```

### **Transcription API**
```json
POST https://api.runpod.ai/v1/{endpoint_id}/run
Content-Type: application/json

{
  "input": {
    "audio_url": "https://example.com/audio.wav",
    "model": "burkimbia/BIA-WHISPER-LARGE-SACHI_V2",
    "language": "moor"
  }
}
```

## 🛠️ Développement Local

### **Build et Test Locaux**
```bash
# Translation Service
cd translation/
docker build --build-arg HF_TOKEN=$HF_TOKEN -t translation-service .
docker run -p 8000:8000 -e HF_TOKEN=$HF_TOKEN translation-service

# Transcription Service  
cd transcription/
docker build --build-arg HF_TOKEN=$HF_TOKEN -t transcription-service .
docker run -p 8001:8000 -e HF_TOKEN=$HF_TOKEN transcription-service

# Speech Service
cd speech/
docker build --build-arg HF_TOKEN=$HF_TOKEN -t speech-service .
docker run -p 8002:8000 -e HF_TOKEN=$HF_TOKEN speech-service
```

## 📋 Modèles Utilisés

| Service | Modèle | Taille | Fonction |
|---------|--------|--------|----------|
| Translation | `burkimbia/BIA-NLLB-600M-5E` | 600M | Neural MT (Français↔Mooré) |
| Translation | `burkimbia/BIA-MISTRAL-7B-SACHI` | 7B | Instruction-tuned MT |
| Transcription | `burkimbia/BIA-WHISPER-LARGE-SACHI_V2` | 1.5B | ASR (Audio→Texte) |
| Speech | *À définir* | - | TTS (Texte→Audio) |

## 🔄 Workflow de Déploiement

1. **Push Code** → GitHub déclenche le build automatique
2. **Build Docker** → Images créées pour chaque service modifié
3. **Push Registry** → Images envoyées vers Docker Hub
4. **Deploy RunPod** → Endpoints créés/mis à jour automatiquement
5. **Health Check** → Vérification du bon fonctionnement

## 📈 Monitoring et Observabilité

- **Logs**: Disponibles via RunPod dashboard
- **Métriques**: Temps de réponse, utilisation GPU
- **Alerts**: Échecs de déploiement via GitHub Actions

## 🚧 Roadmap

- [x] Service de traduction (NLLB + Mistral)
- [x] Service de transcription (Whisper)
- [x] CI/CD multi-services
- [ ] Service de synthèse vocale (TTS)
- [ ] API Gateway unifiée
- [ ] Monitoring avancé
- [ ] Auto-scaling intelligent


