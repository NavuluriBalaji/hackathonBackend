import os
import pickle
from typing import Any, Optional

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "saved_models")

def save_model(model_obj: Any, filename: str) -> str:
    """
    Serializes and saves a trained ML model or model weights into a binary .pkl file.
    """
    if not os.path.exists(MODELS_DIR):
        os.makedirs(MODELS_DIR, exist_ok=True)
    
    if not filename.endswith(".pkl"):
        filename += ".pkl"
        
    filepath = os.path.join(MODELS_DIR, filename)
    with open(filepath, "wb") as f:
        pickle.dump(model_obj, f)
        
    print(f"📦 ML Model successfully saved to pickle file: {filepath}")
    return filepath

def load_model(filename: str) -> Optional[Any]:
    """
    Loads and deserializes a pre-trained ML model or weights from a .pkl file.
    """
    if not filename.endswith(".pkl"):
        filename += ".pkl"
        
    filepath = os.path.join(MODELS_DIR, filename)
    if not os.path.exists(filepath):
        print(f"⚠️ Model pickle file not found at: {filepath}")
        return None
        
    with open(filepath, "rb") as f:
        model_obj = pickle.load(f)
        
    print(f"✅ Loaded ML Model from pickle file: {filepath}")
    return model_obj
