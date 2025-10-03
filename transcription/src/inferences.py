import os
from typing import Optional, Dict, Any
import torch
from transformers import (
    AutoModelForSpeechSeq2Seq, 
    AutoProcessor, 
    pipeline
)
import numpy as np
from loguru import logger


SAMPLE_RATE = 16_000



class Transcriber:
    """
    Audio transcription service using Whisper models.
    """
    
    def __init__(self):
        self.models = {}
        self.processors = {}
        self.pipelines = {}
        
        # Device configuration
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        
        logger.info(f"Transcriber initialized on device: {self.device}")

    def load_model(self, model_path: str):
        """
        Load model and processor from local path or HuggingFace hub.
        
        Args:
            model_path: Local path (e.g., "./models/whisper") or HF model ID
        """
        if model_path not in self.models:
            logger.info(f"Loading model from: {model_path}")
            
            model = AutoModelForSpeechSeq2Seq.from_pretrained(
                model_path,
                torch_dtype=self.torch_dtype,
                low_cpu_mem_usage=True,
                use_safetensors=True
            )
            model.to(self.device)
            
            processor = AutoProcessor.from_pretrained(model_path)
            
            self.models[model_path] = model
            self.processors[model_path] = processor
            
            logger.info(f"Model loaded successfully")

    def get_pipeline(self, model_path: str, is_long_audio: bool = False):
        """
        Get or create transcription pipeline.
        
        The pipeline_key allows caching different pipeline configurations:
        - Same model but different settings (long vs short audio)
        - Avoids recreating pipelines unnecessarily
        """
        # Create unique cache key: model + audio length setting
        pipeline_key = f"{model_path}_long_{is_long_audio}"
        
        if pipeline_key not in self.pipelines:
            if model_path not in self.models:
                self.load_model(model_path)
            
            model = self.models[model_path]
            processor = self.processors[model_path]
            
            pipe_kwargs = {
                "task": "automatic-speech-recognition",
                "model": model,
                "tokenizer": processor.tokenizer,
                "feature_extractor": processor.feature_extractor,
                "torch_dtype": self.torch_dtype,
                "device": self.device,
            }
            
            # Add chunking for long audio
            if is_long_audio:
                pipe_kwargs["chunk_length_s"] = 30
                pipe_kwargs["batch_size"] = 16
                logger.info("Pipeline with chunking enabled")
            
            self.pipelines[pipeline_key] = pipeline(**pipe_kwargs)
        
        return self.pipelines[pipeline_key]

    def transcribe_from_array(
        self, 
        audio_array: np.ndarray, 
        asr_model: str = "burkimbia/BIA-WHISPER-LARGE-SACHI_V2",
        language: Optional[str] = None,
        return_timestamps: bool = False,
        task: str = "transcribe",
        is_long_audio: bool = False,
        **generate_kwargs
    ) -> Dict[str, Any]:
        """
        Transcribe audio array.
        
        Args:
            audio_array: NumPy array at 16kHz
            asr_model: Model to use
            language: Target language (e.g., "english", "french")
            return_timestamps: Return timestamps ("word" or True)
            task: "transcribe" or "translate"
            is_long_audio: Enable chunking for long audio
            
        Returns:
            Dict with transcription results
        """
        try:
            pipe = self.get_pipeline(asr_model, is_long_audio)
            
            # Default generation parameters
            default_kwargs = {
                "max_new_tokens": 448,
                "num_beams": 1,
                "condition_on_prev_tokens": False,
                "compression_ratio_threshold": 1.35,
                "temperature": (0.0, 0.2, 0.4, 0.6, 0.8, 1.0),
                "logprob_threshold": -1.0,
                "no_speech_threshold": 0.6,
            }
            
            if language:
                default_kwargs["language"] = language
            if task:
                default_kwargs["task"] = task
            
            default_kwargs.update(generate_kwargs)
            
            # Transcribe
            result = pipe(
                audio_array,
                return_timestamps=return_timestamps,
                generate_kwargs=default_kwargs
            )
            
            return {
                "text": result.get("text", ""),
                "chunks": result.get("chunks", []) if return_timestamps else [],
                "language": language,
                "task": task,
                "model": asr_model,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            return {
                "text": "",
                "chunks": [],
                "language": language,
                "task": task,
                "model": asr_model,
                "success": False,
                "error": str(e)
            }


asr_client = Transcriber()