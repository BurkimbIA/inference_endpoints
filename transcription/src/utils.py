import os
import io
import base64
from typing import Union, Tuple
import torch
import librosa
import soundfile as sf
import numpy as np
from loguru import logger


def auto_device(cls):
    """
    Decorator to automatically handle device placement for model classes.
    """
    original_init = cls.__init__
    
    def new_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        if hasattr(self, 'model') and hasattr(self.model, 'to'):
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model = self.model.to(device)
            logger.info(f"{cls.__name__} moved to device: {device}")
    
    cls.__init__ = new_init
    return cls


def ensure_device(model, device=None):
    """
    Ensure model is on the correct device.
    """
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    
    if hasattr(model, 'to'):
        return model.to(device)
    return model


def preprocess_audio(
    audio_data: Union[str, bytes, np.ndarray], 
    target_sr: int = 16000,
    normalize: bool = True
) -> Tuple[np.ndarray, int]:
    """
    Preprocess audio data for transcription.
    
    Args:
        audio_data: Audio file path, bytes, or numpy array
        target_sr: Target sample rate
        normalize: Whether to normalize audio
        
    Returns:
        Tuple of (audio_array, sample_rate)
    """
    try:
        if isinstance(audio_data, str):
            # File path
            audio, sr = librosa.load(audio_data, sr=target_sr)
        elif isinstance(audio_data, bytes):
            # Bytes data
            audio, sr = sf.read(io.BytesIO(audio_data))
            if sr != target_sr:
                audio = librosa.resample(audio, orig_sr=sr, target_sr=target_sr)
                sr = target_sr
        elif isinstance(audio_data, np.ndarray):
            # NumPy array
            audio = audio_data
            sr = target_sr
        else:
            raise ValueError(f"Unsupported audio data type: {type(audio_data)}")
        
        # Normalize audio
        if normalize:
            audio = audio / np.max(np.abs(audio)) if np.max(np.abs(audio)) > 0 else audio
        
        return audio, sr
        
    except Exception as e:
        logger.error(f"Audio preprocessing failed: {str(e)}")
        raise


def audio_to_base64(audio_path: str) -> str:
    """
    Convert audio file to base64 string.
    """
    try:
        with open(audio_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
        return base64.b64encode(audio_bytes).decode('utf-8')
    except Exception as e:
        logger.error(f"Failed to convert audio to base64: {str(e)}")
        raise


def base64_to_audio(base64_string: str, output_path: str = None) -> str:
    """
    Convert base64 string to audio file.
    
    Returns path to the saved audio file.
    """
    try:
        audio_bytes = base64.b64decode(base64_string)
        
        if output_path is None:
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            output_path = temp_file.name
            temp_file.close()
        
        with open(output_path, "wb") as audio_file:
            audio_file.write(audio_bytes)
        
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to convert base64 to audio: {str(e)}")
        raise


def validate_audio_format(audio_path: str, max_duration: float = 300.0) -> bool:
    """
    Validate audio file format and duration.
    
    Args:
        audio_path: Path to audio file
        max_duration: Maximum allowed duration in seconds
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Check if file exists
        if not os.path.exists(audio_path):
            logger.error(f"Audio file not found: {audio_path}")
            return False
        
        # Load audio to check format and duration
        audio, sr = librosa.load(audio_path, sr=None)
        duration = len(audio) / sr
        
        if duration > max_duration:
            logger.error(f"Audio duration ({duration:.2f}s) exceeds maximum ({max_duration}s)")
            return False
        
        logger.info(f"Audio validation passed: {duration:.2f}s @ {sr}Hz")
        return True
        
    except Exception as e:
        logger.error(f"Audio validation failed: {str(e)}")
        return False


def split_long_audio(
    audio_path: str, 
    chunk_duration: float = 30.0, 
    overlap: float = 2.0
) -> list:
    """
    Split long audio file into smaller chunks for processing.
    
    Args:
        audio_path: Path to audio file
        chunk_duration: Duration of each chunk in seconds
        overlap: Overlap between chunks in seconds
        
    Returns:
        List of chunk file paths
    """
    try:
        audio, sr = librosa.load(audio_path, sr=None)
        total_duration = len(audio) / sr
        
        if total_duration <= chunk_duration:
            return [audio_path]
        
        chunk_samples = int(chunk_duration * sr)
        overlap_samples = int(overlap * sr)
        step_samples = chunk_samples - overlap_samples
        
        chunks = []
        for start in range(0, len(audio), step_samples):
            end = min(start + chunk_samples, len(audio))
            chunk_audio = audio[start:end]
            
            # Save chunk
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            sf.write(temp_file.name, chunk_audio, sr)
            chunks.append(temp_file.name)
            temp_file.close()
        
        logger.info(f"Split audio into {len(chunks)} chunks")
        return chunks
        
    except Exception as e:
        logger.error(f"Audio splitting failed: {str(e)}")
        raise