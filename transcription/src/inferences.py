import os
import uuid
import logging
import tempfile
from datetime import datetime
from typing import Optional, Dict, Any

import torch
from datasets import Dataset, DatasetDict, concatenate_datasets, Audio, load_dataset, DownloadConfig
from transformers import pipeline
from huggingface_hub import HfApi, login
import torchaudio
import librosa
import soundfile as sf
from loguru import logger

# Configuration
HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    logger.error("Hugging Face token not found. Please set HF_TOKEN environment variable.")
    raise SystemExit

CURRENT_DATASET = "sawadogosalif/Sachi_demo_dataset"
SAMPLE_RATE = 16_000

ASR_MODELS = [
    "burkimbia/BIA-WHISPER-LARGE-SACHI_V2"
]

# Authenticate with Hugging Face
login(token=HF_TOKEN)
api = HfApi(token=HF_TOKEN)


def get_or_create_dataset(dataset_name: str) -> Dataset:
    """
    Load the dataset if it exists, otherwise create a new empty one.
    """
    try:
        ds = load_dataset(
            dataset_name,
            split="train",
            download_config=DownloadConfig(token=HF_TOKEN)
        )
        logger.info(f"Loaded dataset '{dataset_name}' with {len(ds)} examples.")
    except Exception:
        logger.warning(f"Dataset '{dataset_name}' not found or failed to load. Creating a new one.")
        ds = Dataset.from_dict({
            "audio": [],
            "text": [],
            "language": [],
            "datetime": [],
        })
        DatasetDict({"train": ds}).push_to_hub(dataset_name, token=HF_TOKEN)
        logger.info(f"Created empty dataset '{dataset_name}'.")
    return ds


def save_dataset(dataset: Dataset, dataset_name: str) -> None:
    """
    Push the updated dataset back to Hugging Face hub.
    """
    ds_dict = DatasetDict({"train": dataset})
    ds_dict.push_to_hub(dataset_name, token=HF_TOKEN)
    logger.info(f"Pushed updated dataset to '{dataset_name}' ({len(dataset)} records).")


class Transcriber:
    """
    Audio transcription service using Whisper and other ASR models.
    """
    
    def __init__(self):
        self.pipelines = {}
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Transcriber initialized on device: {self.device}")

    def get_pipeline(self, asr_model: str):
        """
        Get or create a transcription pipeline for the specified model.
        """
        if asr_model not in self.pipelines:
            logger.info(f"Loading ASR model: {asr_model}")
            self.pipelines[asr_model] = pipeline(
                "automatic-speech-recognition",
                model=asr_model,
                device=0 if self.device == "cuda" else -1,
                token=HF_TOKEN
            )
            logger.info(f"Model {asr_model} loaded successfully")
        return self.pipelines[asr_model]

    def transcribe(
        self, 
        audio_path: str, 
        asr_model: str = "burkimbia/BIA-WHISPER-LARGE-SACHI_V2",
        language: Optional[str] = None,
        return_timestamps: bool = False
    ) -> Dict[str, Any]:
        """
        Transcribe audio file to text.
        
        Args:
            audio_path: Path to audio file
            asr_model: ASR model to use for transcription
            language: Target language (optional)
            return_timestamps: Whether to return word timestamps
            
        Returns:
            Dictionary containing transcription results
        """
        try:
            pipe = self.get_pipeline(asr_model)
            
            # Process audio
            audio, sr = librosa.load(audio_path, sr=SAMPLE_RATE)
            
            # Transcribe
            result = pipe(
                audio,
                return_timestamps=return_timestamps,
                generate_kwargs={"language": language} if language else {}
            )
            
            return {
                "text": result.get("text", ""),
                "chunks": result.get("chunks", []) if return_timestamps else [],
                "language": language,
                "model": asr_model,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            return {
                "text": "",
                "chunks": [],
                "language": language,
                "model": asr_model,
                "success": False,
                "error": str(e)
            }

    def batch_transcribe(
        self, 
        audio_paths: list, 
        asr_model: str = "burkimbia/BIA-WHISPER-LARGE-SACHI_V2"
    ) -> list:
        """
        Transcribe multiple audio files.
        """
        results = []
        for audio_path in audio_paths:
            result = self.transcribe(audio_path, asr_model)
            results.append(result)
        return results


class DatasetManager:
    """
    Manage transcription datasets on Hugging Face Hub.
    """
    
    def __init__(self, dataset_name: str = CURRENT_DATASET):
        self.dataset_name = dataset_name
        self.dataset = get_or_create_dataset(dataset_name)
    
    def add_transcription(
        self,
        audio_path: str,
        text: str,
        language: str = "moor",
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Add a new transcription to the dataset.
        """
        # Load audio
        audio, sr = librosa.load(audio_path, sr=SAMPLE_RATE)
        
        # Create new record
        new_record = {
            "audio": {"array": audio, "sampling_rate": sr},
            "text": text,
            "language": language,
            "datetime": datetime.now().isoformat(),
        }
        
        # Add metadata if provided
        if metadata:
            new_record.update(metadata)
        
        # Add to dataset
        new_dataset = Dataset.from_dict({k: [v] for k, v in new_record.items()})
        self.dataset = concatenate_datasets([self.dataset, new_dataset])
        
        logger.info(f"Added transcription to dataset. Total records: {len(self.dataset)}")
    
    def save_dataset(self) -> None:
        """
        Save the current dataset to Hugging Face Hub.
        """
        save_dataset(self.dataset, self.dataset_name)


# Initialize global instances
current_dataset = get_or_create_dataset(CURRENT_DATASET)
asr_client = Transcriber()
dataset_manager = DatasetManager()