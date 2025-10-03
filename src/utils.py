"""
Utilitaires pour la gestion des devices (GPU/CPU) et autres fonctions communes
"""

import torch
import functools
from typing import Optional, Dict, Any


def get_device_info() -> Dict[str, Any]:
    """
    Retourne les informations sur le device disponible
    
    Returns:
        Dict contenant les infos du device
    """
    device_info = {
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "cuda_available": torch.cuda.is_available(),
    }
    
    if torch.cuda.is_available():
        device_info.update({
            "gpu_count": torch.cuda.device_count(),
            "current_device": torch.cuda.current_device(),
            "gpu_name": torch.cuda.get_device_name(0),
            "gpu_memory_gb": round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 1),
            "cuda_version": torch.version.cuda
        })
    
    return device_info


def log_device_info(prefix: str = ""):
    """
    Log les informations du device
    
    Args:
        prefix: Préfixe pour les logs (ex: "[ModelName]")
    """
    info = get_device_info()
    device = info["device"]
    
    print(f"{prefix} Using device: {device}")
    
    if info["cuda_available"]:
        print(f"{prefix} GPU: {info['gpu_name']}")
        print(f"{prefix} CUDA Version: {info['cuda_version']}")
        print(f"{prefix} GPU Memory: {info['gpu_memory_gb']} GB")
    else:
        print(f"{prefix} No GPU available, using CPU")


def auto_device(cls):
    """
    Décorateur de classe qui ajoute automatiquement la gestion du device
    
    Usage:
        @auto_device
        class MyModel:
            def __init__(self, model_name):
                # self.device sera automatiquement disponible
                pass
    """
    original_init = cls.__init__
    
    @functools.wraps(original_init)
    def new_init(self, *args, **kwargs):
        # Ajouter les attributs device
        device_info = get_device_info()
        self.device = device_info["device"]
        self.device_info = device_info
        
        # Log device info avec le nom de la classe
        log_device_info(f"[{cls.__name__}]")
        
        # Appeler l'__init__ original
        original_init(self, *args, **kwargs)
    
    cls.__init__ = new_init
    return cls


def ensure_device(tensor_or_inputs, device: Optional[str] = None):
    """
    S'assure qu'un tensor ou des inputs sont sur le bon device
    
    Args:
        tensor_or_inputs: Tensor PyTorch ou dict d'inputs
        device: Device cible (si None, utilise auto-détection)
    
    Returns:
        Tensor/inputs sur le device approprié
    """
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    
    if torch.is_tensor(tensor_or_inputs):
        return tensor_or_inputs.to(device)
    elif hasattr(tensor_or_inputs, 'to'):  # Pour les inputs de tokenizer
        return tensor_or_inputs.to(device)
    else:
        return tensor_or_inputs