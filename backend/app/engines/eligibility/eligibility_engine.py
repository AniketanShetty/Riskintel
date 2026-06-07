"""
eligibility_engine.py

Eligibility Engine (E1) - binary classification using a Random Forest model.
Calculates local explainability using treeinterpreter.
"""
import os
import sys
import joblib
import pandas as pd
from typing import Dict, Any

# Polyfill for distutils to fix treeinterpreter on Python 3.12+
if 'distutils' not in sys.modules:
    import types
    distutils = types.ModuleType('distutils')
    distutils.version = types.ModuleType('distutils.version')
    class LooseVersion:
        def __init__(self, v): self.v = str(v)
        def __lt__(self, other): return self.v < str(other.v)
        def __ge__(self, other): return self.v >= str(other.v)
    distutils.version.LooseVersion = LooseVersion
    sys.modules['distutils'] = distutils
    sys.modules['distutils.version'] = distutils.version

from treeinterpreter import treeinterpreter as ti

class EligibilityEngine:
    """Eligibility Engine utilizing a trained Random Forest model and treeinterpreter."""
    _cached_model = None

    def __init__(self, model_path: str = None):
        """Initialize and load the model."""
        if model_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(
                current_dir, '..', '..', '..', '..',
                'models', 'eligibility', 'random_forest.joblib'
            )
        self.model_path = model_path
        self._load_model()

    def _load_model(self):
        """Loads and caches the Random Forest model."""
        if EligibilityEngine._cached_model is None:
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Model file not found at {self.model_path}")
            EligibilityEngine._cached_model = joblib.load(self.model_path)
        self.model = EligibilityEngine._cached_model

    def evaluate_eligibility(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate loan eligibility based on input features.
        
        Args:
            features: Dictionary containing applicant inputs.
            
        Returns:
            Dictionary with verdict, probability, bias, and feature_contributions.
        """
        # Form encoding translations
        edu_raw = features.get('education')
        if isinstance(edu_raw, str):
            edu_encoded = 1 if edu_raw.strip().lower() == 'graduate' else 0
        else:
            edu_encoded = int(edu_raw) if edu_raw is not None else 0

        se_raw = features.get('self_employed')
        if isinstance(se_raw, str):
            se_encoded = 1 if se_raw.strip().lower() == 'yes' else 0
        else:
            se_encoded = int(se_raw) if se_raw is not None else 0

        # Exact columns expected by the model
        cols = [
            "dependents", "education", "self_employed", "annual_income", 
            "loan_amount", "loan_term", "cibil_score", 
            "residential_assets_value", "commercial_assets_value", 
            "luxury_assets_value", "bank_asset_value"
        ]
        
        # Build feature dict
        input_dict = {
            "dependents": int(features.get("dependents", 0)),
            "education": edu_encoded,
            "self_employed": se_encoded,
            "annual_income": float(features.get("annual_income", 0)),
            "loan_amount": float(features.get("loan_amount", 0)),
            "loan_term": float(features.get("loan_term", 0)),
            "cibil_score": float(features.get("cibil_score", 0)),
            "residential_assets_value": float(features.get("residential_assets_value", 0)),
            "commercial_assets_value": float(features.get("commercial_assets_value", 0)),
            "luxury_assets_value": float(features.get("luxury_assets_value", 0)),
            "bank_asset_value": float(features.get("bank_asset_value", 0))
        }

        df = pd.DataFrame([input_dict], columns=cols)

        # Run treeinterpreter predict
        try:
            prediction, bias, contributions = ti.predict(self.model, df)
        except Exception as e:
            raise ValueError(f"Model prediction failed: {e}")
        
        pos_idx = 1
        prob = float(prediction[0][pos_idx])
        base_bias = float(bias[0][pos_idx])
        
        # Extract contributions
        contribs = {}
        for idx, col in enumerate(cols):
            contribs[col] = float(contributions[0][idx][pos_idx])

        # Map prob to verdict
        if prob >= 0.80:
            verdict = "Highly Likely"
        elif prob >= 0.60:
            verdict = "Likely"
        elif prob >= 0.40:
            verdict = "Borderline"
        else:
            verdict = "Unlikely"

        return {
            "verdict": verdict,
            "probability": round(prob, 4),
            "bias": round(base_bias, 4),
            "feature_contributions": {col: round(val, 4) for col, val in contribs.items()}
        }

def get_eligibility(features: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience wrapper for Eligibility Engine."""
    engine = EligibilityEngine()
    return engine.evaluate_eligibility(features)
