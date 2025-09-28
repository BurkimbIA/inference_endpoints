"""
RunPod Serverless Handler for Mistral and NLLB Translation Models
"""

import os
import sys
import json
import traceback
import time
from typing import Dict, Any, Optional
import runpod
from loguru import logger

sys.path.append(os.path.dirname(__file__))

from inferences import MistralTranslator, NLLBTranslator
from monitoring import (
    initialize_monitoring, 
    get_health_status, 
    get_performance_metrics,
    record_request_performance
)

mistral_model = None
nllb_model = None

def load_models():
    """Load models on cold start to optimize performance"""
    global mistral_model, nllb_model
    
    try:
        # Load Mistral model
        logger.info("Loading Mistral model: burkimbia/BIA-MISTRAL-7B-SACHI")
        mistral_model = MistralTranslator(model_id="burkimbia/BIA-MISTRAL-7B-SACHI")
        logger.info("Mistral model loaded successfully")
        
        # Load NLLB model
        logger.info("Loading NLLB model: burkimbia/BIA-NLLB-600M-5E")
        nllb_model = NLLBTranslator(model_name="burkimbia/BIA-NLLB-600M-5E")
        logger.info("NLLB model loaded successfully")
        
        # Initialize monitoring with loaded models
        models = {
            "mistral": mistral_model,
            "nllb": nllb_model
        }
        initialize_monitoring(models)
        logger.info("Monitoring initialized successfully")
            
    except Exception as e:
        logger.error(f"Error loading models: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def validate_translation_input(job_input: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and normalize translation input parameters"""
    
    # Required fields
    text = job_input.get("text")
    if not text or not isinstance(text, str):
        raise ValueError("'text' field is required and must be a non-empty string")
    
    model_type = job_input.get("model_type", "").lower()
    if model_type not in ["mistral", "nllb"]:
        raise ValueError("'model_type' must be either 'mistral' or 'nllb'")
    
    src_lang = job_input.get("src_lang")
    tgt_lang = job_input.get("tgt_lang")
    
    if not src_lang or not tgt_lang:
        raise ValueError("Both 'src_lang' and 'tgt_lang' are required")
    
    # Validate language codes based on model type
    if model_type == "mistral":
        valid_langs = ["fra_Latn", "moor_Latn"]
        if src_lang not in valid_langs or tgt_lang not in valid_langs:
            raise ValueError(f"For Mistral model, languages must be in {valid_langs}")
    
    elif model_type == "nllb":
        valid_langs = ["moor_Latn", "fr_Latn", "en_Latn"]
        if src_lang not in valid_langs or tgt_lang not in valid_langs:
            logger.warning(f"Language {src_lang} or {tgt_lang} might not be supported by NLLB model")
    
    generation_params = {}
    if model_type == "nllb":
        generation_params = {
            "a": job_input.get("a", 32),
            "b": job_input.get("b", 3),
            "max_input_length": job_input.get("max_input_length", 1024),
            "num_beams": job_input.get("num_beams", 5)
        }
    
    return {
        "text": text,
        "model_type": model_type,
        "src_lang": src_lang,
        "tgt_lang": tgt_lang,
        "generation_params": generation_params
    }

def translate_text(validated_input: Dict[str, Any]) -> str:
    """Perform translation using the specified model"""
    
    text = validated_input["text"]
    model_type = validated_input["model_type"]
    src_lang = validated_input["src_lang"]
    tgt_lang = validated_input["tgt_lang"]
    generation_params = validated_input["generation_params"]
    
    if model_type == "mistral":
        if mistral_model is None:
            raise RuntimeError("Mistral model not loaded.")
        
        return mistral_model.translate(text, src_lang, tgt_lang)
    
    elif model_type == "nllb":
        if nllb_model is None:
            raise RuntimeError("NLLB model not loaded.")
        
        return nllb_model.translate(
            text, 
            src_lang, 
            tgt_lang, 
            **generation_params
        )

def handler(job):
    """
    RunPod serverless handler function
    
    Expected input format:
    {
        "text": "Text to translate",
        "model_type": "mistral" | "nllb",
        "src_lang": "source_language_code",
        "tgt_lang": "target_language_code",
        
        # Optional NLLB parameters
        "a": 32,
        "b": 3,
        "max_input_length": 1024,
        "num_beams": 5
    }
    
    Returns:
    {
        "translated_text": "Translated text",
        "model_type": "mistral" | "nllb",
        "src_lang": "source_language_code",
        "tgt_lang": "target_language_code",
        "success": true
    }
    """
    job_input = job["input"]
    start_time = time.time()
    
    try:
        logger.info(f"Received translation request: {job_input}")
        
        if job_input.get("action") == "health":
            return get_health_status()
        
        if job_input.get("action") == "metrics":
            return get_performance_metrics()
        
        validated_input = validate_translation_input(job_input)
        translated_text = translate_text(validated_input)
        
        duration = time.time() - start_time
        record_request_performance(duration, success=True)
        
        response = {
            "translated_text": translated_text,
            "model_type": validated_input["model_type"],
            "src_lang": validated_input["src_lang"],
            "tgt_lang": validated_input["tgt_lang"],
            "processing_time_ms": duration * 1000,
            "success": True
        }
        
        logger.info(f"Translation completed successfully in {duration:.3f}s")
        return response
        
    except ValueError as e:
        duration = time.time() - start_time
        record_request_performance(duration, success=False)
        logger.error(f"Validation error: {str(e)}")
        return {
            "error": f"Input validation error: {str(e)}",
            "success": False
        }
        
    except RuntimeError as e:
        duration = time.time() - start_time
        record_request_performance(duration, success=False)
        logger.error(f"Runtime error: {str(e)}")
        return {
            "error": f"Model runtime error: {str(e)}",
            "success": False
        }
        
    except Exception as e:
        duration = time.time() - start_time
        record_request_performance(duration, success=False)
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "error": f"Internal server error: {str(e)}",
            "success": False
        }

def health_check():
    """Health check endpoint to verify models are loaded"""
    
    status = {
        "mistral_loaded": mistral_model is not None,
        "nllb_loaded": nllb_model is not None,
        "hf_token_configured": os.environ.get("HF_TOKEN") is not None,
        "status": "healthy"
    }
    
    if not status["mistral_loaded"] and not status["nllb_loaded"]:
        status["status"] = "unhealthy - no models loaded"
        
    return status

if __name__ == "__main__":
    # Load models on startup
    logger.info("Loading models...")
    load_models()
    logger.info("Models loaded successfully")
    
    # Start RunPod serverless
    runpod.serverless.start({"handler": handler})