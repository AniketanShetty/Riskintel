import os
import pickle
import joblib
from pathlib import Path

def test_ml_models_are_deterministic():
    """
    Smoke test to verify that the persisted ML models were trained with
    a fixed random_state to ensure reproducibility across rebuilds.
    """
    root = Path(__file__).parent.parent.parent
    
    rf_path = root / "models" / "eligibility" / "random_forest.joblib"
    if rf_path.exists():
        rf_model = joblib.load(rf_path)
        assert getattr(rf_model, "random_state", None) == 42, "RandomForest must be trained with random_state=42"

    kmeans_path = root / "models" / "archetype" / "kmeans_model.pkl"
    if kmeans_path.exists():
        with open(kmeans_path, "rb") as f:
            kmeans_model = pickle.load(f)
        assert getattr(kmeans_model, "random_state", None) == 42, "KMeans must be trained with random_state=42"

def test_ml_training_scripts_are_deterministic():
    """
    Smoke test to ensure ML training scripts strictly use random_state=42 
    to guarantee reproducibility.
    """
    root = Path(__file__).parent.parent.parent
    scripts = [
        root / "scripts" / "train_borrower_archetype.py",
        root / "backend" / "app" / "engines" / "eligibility" / "train.py"
    ]
    
    for script_path in scripts:
        if script_path.exists():
            content = script_path.read_text(encoding="utf-8")
            assert "random_state=42" in content, f"random_state=42 missing in {script_path.name}"
