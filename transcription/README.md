# 🎤 Audio Transcription Service

Un service d'inférence simple et efficace pour la transcription audio utilisant les modèles Whisper.

## 🚀 Fonctionnalités

- Transcription audio en temps réel
- Support de fichiers audio via URL ou base64
- Modèles Whisper optimisés pour les langues locales
- API simple et rapide
- Traitement par lots (batch)
- Health check intégré

## 🤖 Modèles

### Whisper Fine-tuned pour Mooré
- **Modèle**: `burkimbia/BIA-WHISPER-LARGE-SACHI_V2`
- **Usage**: Transcription automatique pour le Mooré et autres langues

## 🛠️ Installation et Utilisation

### Construction de l'image Docker

```bash
cd transcription/
docker build --build-arg HF_TOKEN=$HF_TOKEN -t burkimbia/transcription-service .
```

### Lancement du service

```bash
docker run -p 8000:8000 -e HF_TOKEN=$HF_TOKEN burkimbia/transcription-service
```

## 📋 API

### Transcription Simple

```json
{
  "input": {
    "audio_url": "https://example.com/audio.wav",
    "model": "burkimbia/BIA-WHISPER-LARGE-SACHI_V2",
    "language": "moor",
    "return_timestamps": false
  }
}
```

### Transcription par Lots

```json
{
  "input": {
    "audio_urls": [
      "https://example.com/audio1.wav",
      "https://example.com/audio2.wav"
    ],
    "model": "burkimbia/BIA-WHISPER-LARGE-SACHI_V2",
    "language": "moor"
  }
}
```

### Audio en Base64

```json
{
  "input": {
    "audio_base64": "base64_encoded_audio_data_here",
    "model": "burkimbia/BIA-WHISPER-LARGE-SACHI_V2",
    "language": "moor"
  }
}
```

## 📤 Format de Réponse

```json
{
  "text": "Texte transcrit",
  "chunks": [
    {
      "text": "mot",
      "timestamp": [0.0, 1.0]
    }
  ],
  "language": "moor",
  "model": "burkimbia/BIA-WHISPER-LARGE-SACHI_V2",
  "success": true
}
```

## 📁 Structure Simplifiée

```
transcription/
├── src/
│   ├── handler.py          # Handlers RunPod
│   ├── inferences.py       # Logique de transcription
│   └── utils.py           # Utilitaires audio
├── requirements.txt        # Dépendances minimales
├── Dockerfile             # Image Docker
└── README.md             # Documentation
```

## ✨ Optimisations

Ce service est maintenant optimisé pour l'inférence pure :
- ✅ Code minimal et maintenable
- ✅ Pas de sauvegarde de dataset
- ✅ Focus sur la performance
- ✅ Dépendances réduites
- ✅ Démarrage plus rapide