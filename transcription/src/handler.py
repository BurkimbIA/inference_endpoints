import os
import json
import tempfile
from typing import Dict, Any, List
import runpod
from loguru import logger

from inferences import asr_client, ASR_MODELS, dataset_manager


def transcribe_audio(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    RunPod handler for audio transcription.
    
    Expected input format:
    {
        "audio_url": "https://example.com/audio.wav",  # or base64 audio data
        "audio_base64": "base64_encoded_audio_data",   # alternative to audio_url
        "model": "burkimbia/BIA-WHISPER-LARGE-SACHI_V2",  # optional
        "language": "moor",  # optional
        "return_timestamps": false,  # optional
        "save_to_dataset": false  # optional
    }
    """
    try:
        job_input = job.get("input", {})
        
        # Get parameters
        audio_url = job_input.get("audio_url")
        audio_base64 = job_input.get("audio_base64")
        model = job_input.get("model", ASR_MODELS[0])
        language = job_input.get("language")
        return_timestamps = job_input.get("return_timestamps", False)
        save_to_dataset = job_input.get("save_to_dataset", False)
        
        # Validate input
        if not audio_url and not audio_base64:
            return {
                "error": "Either 'audio_url' or 'audio_base64' must be provided"
            }
        
        if model not in ASR_MODELS:
            return {
                "error": f"Model '{model}' not supported. Available models: {ASR_MODELS}"
            }
        
        # Handle audio input
        if audio_base64:
            # Decode base64 audio
            import base64
            audio_data = base64.b64decode(audio_base64)
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            temp_file.write(audio_data)
            temp_file.close()
            audio_path = temp_file.name
        else:
            # Download audio from URL
            import requests
            response = requests.get(audio_url)
            response.raise_for_status()
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            temp_file.write(response.content)
            temp_file.close()
            audio_path = temp_file.name
        
        # Transcribe audio
        logger.info(f"Transcribing audio with model: {model}")
        result = asr_client.transcribe(
            audio_path=audio_path,
            asr_model=model,
            language=language,
            return_timestamps=return_timestamps
        )
        
        # Save to dataset if requested
        if save_to_dataset and result["success"] and result["text"]:
            try:
                dataset_manager.add_transcription(
                    audio_path=audio_path,
                    text=result["text"],
                    language=language or "unknown",
                    metadata={
                        "model": model,
                        "source": "api_request"
                    }
                )
                dataset_manager.save_dataset()
                result["saved_to_dataset"] = True
            except Exception as e:
                logger.warning(f"Failed to save to dataset: {str(e)}")
                result["saved_to_dataset"] = False
        
        # Clean up temporary file
        try:
            os.unlink(audio_path)
        except:
            pass
        
        return result
        
    except Exception as e:
        logger.error(f"Transcription job failed: {str(e)}")
        return {
            "error": str(e),
            "success": False
        }


def batch_transcribe_audio(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    RunPod handler for batch audio transcription.
    
    Expected input format:
    {
        "audio_urls": ["https://example.com/audio1.wav", "https://example.com/audio2.wav"],
        "model": "burkimbia/BIA-WHISPER-LARGE-SACHI_V2",  # optional
        "language": "moor"  # optional
    }
    """
    try:
        job_input = job.get("input", {})
        
        audio_urls = job_input.get("audio_urls", [])
        model = job_input.get("model", ASR_MODELS[0])
        language = job_input.get("language")
        
        if not audio_urls:
            return {"error": "No audio URLs provided"}
        
        results = []
        for i, audio_url in enumerate(audio_urls):
            logger.info(f"Processing audio {i+1}/{len(audio_urls)}")
            
            # Create individual job for each audio
            individual_job = {
                "input": {
                    "audio_url": audio_url,
                    "model": model,
                    "language": language
                }
            }
            
            result = transcribe_audio(individual_job)
            results.append({
                "audio_url": audio_url,
                "result": result
            })
        
        return {
            "results": results,
            "total_processed": len(results),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Batch transcription job failed: {str(e)}")
        return {
            "error": str(e),
            "success": False
        }


# Health check endpoint
def health_check(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Health check endpoint.
    """
    return {
        "status": "healthy",
        "available_models": ASR_MODELS,
        "service": "transcription"
    }


if __name__ == "__main__":
    logger.info("Starting Transcription Service...")
    logger.info(f"Available models: {ASR_MODELS}")
    
    # Start RunPod serverless worker
    runpod.serverless.start({
        "handler": transcribe_audio,
        "batch_handler": batch_transcribe_audio,
        "health_check": health_check
    })