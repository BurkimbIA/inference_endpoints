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
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(__file__))

from inferences import MistralTranslator, NLLBTranslator
from utils import get_device_info
from monitoring import (
    initialize_monitoring,
    get_health_status,
    get_performance_metrics,
    record_request_performance,
)

# Cache des modèles chargés
loaded_models = {}


def load_model(model_type: str):
    """
    Charge un modèle spécifique à la demande
    
    Args:
        model_type: Type de modèle à charger ("mistral" ou "nllb")
    
    Returns:
        Le modèle chargé
    """

    # Vérifier si le modèle est déjà chargé
    if model_type in loaded_models:
        logger.info(f"Model {model_type} already loaded, using cached version")
        return loaded_models[model_type]

    try:
        # Map model_type to model key
        if model_type == "mistral":
            model_key = "burkimbia/BIA-MISTRAL-7B-SACHI"
            logger.info(f"Loading Mistral model: {model_key}")
            model = MistralTranslator(model_id=model_key)
            logger.info("Mistral model loaded successfully")

        elif model_type == "nllb":
            local_model_path = "/app/models/BIA-NLLB-600M-5E"
            if os.path.exists(local_model_path):
                model_name = local_model_path
                logger.info(f"Loading NLLB model from local path: {model_name}")
                model = NLLBTranslator(model_name=model_name)
            else:
                model_name = "burkimbia/BIA-NLLB-600M-5E"
                logger.warning(f"Local NLLB model path not found, loading from HuggingFace: {model_name}")
                model = NLLBTranslator(model_name=model_name)
            
            logger.info("NLLB model loaded successfully")
            
        else:
            raise ValueError(f"Unknown model type: {model_type}")

        loaded_models[model_type] = model

        initialize_monitoring({model_type: model})
        logger.info(f"Monitoring initialized for {model_type} model")

        return model

    except Exception as e:
        logger.error(f"Error loading {model_type} model: {str(e)}")
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

    if model_type == "mistral":
        valid_langs = ["fra_Latn", "moor_Latn"]
        if src_lang not in valid_langs or tgt_lang not in valid_langs:
            raise ValueError(f"For Mistral model, languages must be in {valid_langs}")

    elif model_type == "nllb":
        valid_langs = ["moor_Latn", "fr_Latn", "fra_Latn", "en_Latn"]
        if src_lang not in valid_langs or tgt_lang not in valid_langs:
            logger.warning(
                f"Language {src_lang} or {tgt_lang} might not be supported by NLLB model"
            )

    # Optional parameters for both models
    max_tokens = job_input.get("max_tokens")
    if max_tokens is not None and (not isinstance(max_tokens, int) or max_tokens <= 0):
        raise ValueError("'max_tokens' must be a positive integer")

    generation_params = {}
    if model_type == "mistral":
        generation_params = {
            "max_tokens": max_tokens or 512,  # Default for Mistral
        }
    elif model_type == "nllb":
        generation_params = {
            "a": job_input.get("a", 32),
            "b": job_input.get("b", 3),
            "max_input_length": job_input.get("max_input_length", 1024),
            "max_tokens": max_tokens,  # Can be None to use a+b formula
            "num_beams": job_input.get("num_beams", 5),
        }

    return {
        "text": text,
        "model_type": model_type,
        "src_lang": src_lang,
        "tgt_lang": tgt_lang,
        "generation_params": generation_params,
    }


def translate_text(validated_input: Dict[str, Any]) -> str:
    """Perform translation using the specified model"""

    text = validated_input["text"]
    model_type = validated_input["model_type"]
    src_lang = validated_input["src_lang"]
    tgt_lang = validated_input["tgt_lang"]
    generation_params = validated_input["generation_params"]

    model = load_model(model_type)

    if model_type == "mistral":
        return model.translate(
            text, src_lang, tgt_lang, max_tokens=generation_params["max_tokens"]
        )

    elif model_type == "nllb":
        return model.translate(text, src_lang, tgt_lang, **generation_params)


def handler(job):
    """
    RunPod serverless handler function

    Expected input format:
    {
        "text": "Text to translate",
        "model_type": "mistral" | "nllb",
        "src_lang": "source_language_code",
        "tgt_lang": "target_language_code",

        # Optional parameters for both models
        "max_tokens": 512,  # Maximum tokens to generate (default: 512 for Mistral, dynamic for NLLB)

        # Optional NLLB-specific parameters (used only when max_tokens is not provided)
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
            health_status = get_health_status()
            # Add device information to health status
            health_status["device_info"] = get_device_info()
            return health_status

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
            "success": True,
        }

        logger.info(f"Translation completed successfully in {duration:.3f}s")
        return response

    except ValueError as e:
        duration = time.time() - start_time
        record_request_performance(duration, success=False)
        logger.error(f"Validation error: {str(e)}")
        return {"error": f"Input validation error: {str(e)}", "success": False}

    except RuntimeError as e:
        duration = time.time() - start_time
        record_request_performance(duration, success=False)
        logger.error(f"Runtime error: {str(e)}")
        return {"error": f"Model runtime error: {str(e)}", "success": False}

    except Exception as e:
        duration = time.time() - start_time
        record_request_performance(duration, success=False)
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        return {"error": f"Internal server error: {str(e)}", "success": False}


if __name__ == "__main__":
    logger.info("RunPod serverless handler started")
    logger.info("Models will be loaded on-demand when first requested")
    runpod.serverless.start({"handler": handler})