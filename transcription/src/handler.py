import os
import json
import base64
import io
from typing import Dict, Any, List
import runpod
import requests
import librosa
import soundfile as sf
import numpy as np
from loguru import logger

from inferences import asr_client

MODEL_PATH = "/app/models/BIA-WHISPER-LARGE-SACHI_V2"

def process_audio_direct(audio_base64: str = None, audio_url: str = None) -> tuple:
    """
    Process audio input DIRECTLY - returns audio array and duration.
    
    Args:
        audio_base64: Base64 encoded audio data
        audio_url: URL to download audio from
    
    Returns:
        tuple: (audio_array, duration_seconds)
    """
    try:
        if audio_base64:
            audio_data = base64.b64decode(audio_base64.strip())            
            audio_buffer = io.BytesIO(audio_data)
            audio, sr = sf.read(audio_buffer)
            
        elif audio_url:
            logger.info(f"Downloading audio from: {audio_url}")
            response = requests.get(audio_url, timeout=30)
            response.raise_for_status()
            
            audio_buffer = io.BytesIO(response.content)
            audio, sr = sf.read(audio_buffer)
            
        else:
            raise ValueError("No audio source provided")
        
        
        duration = len(audio) / sr
            
        logger.info(f"Audio processed: shape={audio.shape}, duration={duration:.2f}s, dtype={audio.dtype}")
        return audio, duration
        
    except Exception as e:
        raise Exception(f"Audio processing failed: {str(e)}")


def transcribe_audio(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    RunPod handler for audio transcription using HuggingFace Whisper best practices.
    
    Expected input format:
    {
        "audio_url": "https://example.com/audio.wav",          # or base64 audio data
        "audio_base64": "base64_encoded_audio_data",           # alternative to audio_url
        "model": "burkimbia/BIA-WHISPER-LARGE-SACHI_V2",       # optional
        "language": "english",                                 # optional (e.g., "english", "french", "spanish")
        "task": "transcribe",                                  # optional: "transcribe" or "translate"
        "return_timestamps": false,                            # optional: false, true (sentence), or "word"
        "is_long_audio": false,                                # optional: if true, enables chunking (batch processing)
        "generate_kwargs": {                                   # optional: advanced generation parameters
            "max_new_tokens": 448,
            "temperature": [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
            "compression_ratio_threshold": 1.35,
            "logprob_threshold": -1.0,
            "no_speech_threshold": 0.6
        }
    }
    
    Note: Set is_long_audio=true for audio > 30s for faster batch processing
    
    Returns:
    {
        "text": "transcription text",
        "chunks": [...],                    # if return_timestamps is set
        "language": "english",
        "task": "transcribe",
        "model": "model_name",
        "duration_seconds": 45.2,
        "is_long_audio": true,
        "success": true
    }
    """
    try:
        job_input = job.get("input", {})
        
        audio_url = job_input.get("audio_url")
        audio_base64 = job_input.get("audio_base64")
        model = job_input.get("model", MODEL_PATH)
        language = job_input.get("language")
        task = job_input.get("task", "transcribe")
        return_timestamps = job_input.get("return_timestamps", False)
        is_long_audio = job_input.get("is_long_audio", False)
        generate_kwargs = job_input.get("generate_kwargs", {})
        
        if not audio_url and not audio_base64:
            return {
                "error": "Either 'audio_url' or 'audio_base64' must be provided",
                "success": False
            }

        
        if task not in ["transcribe", "translate"]:
            return {
                "error": f"Task must be 'transcribe' or 'translate', got: {task}",
                "success": False
            }
        
        try:
            logger.info("Processing audio input...")
            audio_array, duration = process_audio_direct(
                audio_base64=audio_base64,
                audio_url=audio_url
            )
        except Exception as e:
            logger.error(f"Audio processing error: {str(e)}")
            return {
                "error": str(e),
                "success": False
            }
        
        # Configure chunking based on is_long_audio parameter
        chunk_length_s = None
        batch_size = 16
        
        if is_long_audio:
            chunk_length_s = 30
            batch_size = 16
            logger.info(f"Long audio mode enabled: chunk_length_s=30, batch_size=16")
        else:
            logger.info(f"Standard mode: sequential processing")
        
        # Transcribe audio directly from memory using HuggingFace best practices
        logger.info(f"Transcribing with model: {model}, language: {language}, task: {task}")
        logger.info(f"Audio duration: {duration:.2f}s")
        
        result = asr_client.transcribe_from_array(
            audio_array=audio_array,
            asr_model=model,
            language=language,
            return_timestamps=return_timestamps,
            task=task,
            chunk_length_s=chunk_length_s,
            batch_size=batch_size,
            **generate_kwargs
        )
        
        result["duration_seconds"] = round(duration, 2)
        result["is_long_audio"] = is_long_audio
        
        logger.info(f"Transcription completed: success={result.get('success')}, duration={duration:.2f}s")
        
        return result
        
    except Exception as e:
        logger.error(f"Transcription job failed: {str(e)}")
        return {
            "error": str(e),
            "success": False
        }





if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Starting Transcription Service with HuggingFace Whisper")
    logger.info("=" * 60)
    logger.info(f"Available models: {ASR_MODELS}")
    logger.info("Service follows HuggingFace best practices for Whisper models")
    logger.info("=" * 60)
    
    # Start RunPod serverless worker
    runpod.serverless.start({
        "handler": transcribe_audio,
    })