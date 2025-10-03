# Transcription Service

This service provides audio transcription capabilities using Whisper and other ASR models.

## Models

### Whisper Fine-tuned for Mooré
- **Model**: `burkimbia/BIA-WHISPER-LARGE-SACHI_V2`
- **Location**: Pre-loaded in Docker image at `/app/models/BIA-WHISPER-LARGE-SACHI_V2`
- **Use case**: Speech-to-text for Mooré language and multilingual audio

## Features

- **Audio Transcription**: Convert audio files to text
- **Batch Processing**: Transcribe multiple audio files at once
- **Dataset Management**: Save transcriptions to Hugging Face datasets
- **Multiple Input Formats**: Support for URLs and base64 encoded audio
- **Timestamp Support**: Optional word-level timestamps
- **Language Detection**: Automatic or manual language specification

## Building the Docker Image

```bash
cd transcription/
docker build --build-arg HF_TOKEN=$HF_TOKEN -t burkimbia/transcription-service .
```

## Running the Service

```bash
docker run -p 8000:8000 -e HF_TOKEN=$HF_TOKEN burkimbia/transcription-service
```

## API Usage

### Single Audio Transcription

```json
{
  "input": {
    "audio_url": "https://example.com/audio.wav",
    "model": "burkimbia/BIA-WHISPER-LARGE-SACHI_V2",
    "language": "moor",
    "return_timestamps": false,
    "save_to_dataset": false
  }
}
```

### Batch Audio Transcription

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

### Base64 Audio Input

```json
{
  "input": {
    "audio_base64": "base64_encoded_audio_data_here",
    "model": "burkimbia/BIA-WHISPER-LARGE-SACHI_V2",
    "language": "moor"
  }
}
```

## Response Format

```json
{
  "text": "Transcribed text content",
  "chunks": [
    {
      "text": "word",
      "timestamp": [0.0, 1.0]
    }
  ],
  "language": "moor",
  "model": "burkimbia/BIA-WHISPER-LARGE-SACHI_V2",
  "success": true
}
```