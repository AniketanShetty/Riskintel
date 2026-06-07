"""
lineage.py

Manages model lineage tracking, validating existence of models and calculating cryptographic hashes.
"""
import os
import hashlib
from typing import Dict

# Paths are resolved relative to the workspace root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
E1_MODEL_PATH = os.path.join(BASE_DIR, "models", "eligibility", "random_forest.joblib")
E2_THRESHOLDS_PATH = os.path.join(BASE_DIR, "data", "processed", "risk_tier_thresholds.json")
E3_SCALER_PATH = os.path.join(BASE_DIR, "models", "archetype", "scaler.pkl")
E3_KMEANS_PATH = os.path.join(BASE_DIR, "models", "archetype", "kmeans_model.pkl")

def calculate_sha256(filepath: str) -> str:
    """Calculate the sha256 hash of a file or return missing/empty."""
    if not os.path.exists(filepath):
        return "missing"
    
    sha256 = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return f"sha256:{sha256.hexdigest()}"
    except Exception:
        return "error"

def get_model_lineage_bind() -> Dict[str, str]:
    """
    Returns the model lineage dictionary containing SHA256 hashes of the models.
    Satisfies FROZEN_ORCHESTRATOR_SPEC_V1.0.
    """
    return {
        "e1_rf_hash": calculate_sha256(E1_MODEL_PATH),
        "e2_thresholds_hash": calculate_sha256(E2_THRESHOLDS_PATH),
        "e3_scaler_hash": calculate_sha256(E3_SCALER_PATH),
        "e3_kmeans_hash": calculate_sha256(E3_KMEANS_PATH)
    }

def verify_models_exist() -> bool:
    """
    Checks if all required model files exist on disk.
    Used by readiness health checks.
    """
    # Critical files are E1 model and E2 thresholds, as well as E3 scaler/kmeans files
    critical_files = [E1_MODEL_PATH, E2_THRESHOLDS_PATH, E3_SCALER_PATH, E3_KMEANS_PATH]
    return all(os.path.exists(f) for f in critical_files)
