import os
import json
import pickle
import pandas as pd
from typing import Dict, Any

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
MODEL_DIR = os.path.join(BASE_DIR, '..', 'models', 'archetype')
DEFINITIONS_PATH = os.path.join(BASE_DIR, '..', 'data', 'processed', 'borrower_archetype_definitions.json')

# Ordinal Mapping
EDUCATION_MAP = {
    'OTHERS': 0,
    'SSC': 1,
    '10TH': 1,
    '12TH': 2,
    'UNDER GRADUATE': 3,
    'GRADUATE': 4,
    'POST-GRADUATE': 5,
    'PROFESSIONAL': 6
}

class BorrowerArchetypeEngine:
    """Engine for determining borrower archetype based on demographic and behavioral features."""

    _cached_scaler = None
    _cached_model = None
    _cached_definitions = None

    def __init__(self):
        """Initialize the archetype engine and load models if not cached."""
        self._load_models()

    @classmethod
    def _load_models(cls):
        """Load the scaling, clustering models and definitions."""
        if cls._cached_scaler is None:
            try:
                with open(os.path.join(MODEL_DIR, 'scaler.pkl'), 'rb') as f:
                    cls._cached_scaler = pickle.load(f)
            except Exception as e:
                raise FileNotFoundError(f"Failed to load scaler.pkl: {e}")

        if cls._cached_model is None:
            try:
                with open(os.path.join(MODEL_DIR, 'kmeans_model.pkl'), 'rb') as f:
                    cls._cached_model = pickle.load(f)
            except Exception as e:
                raise FileNotFoundError(f"Failed to load kmeans_model.pkl: {e}")

        if cls._cached_definitions is None:
            try:
                with open(DEFINITIONS_PATH, 'r') as f:
                    # JSON keys are always strings, map them back to int
                    raw_defs = json.load(f)
                    cls._cached_definitions = {int(k): v for k, v in raw_defs.items()}
            except Exception as e:
                raise FileNotFoundError(f"Failed to load definitions JSON: {e}")

    def _map_education(self, val: Any) -> int:
        """Map education string to ordinal value."""
        if pd.isna(val) or val is None:
            return 0
        val_str = str(val).strip().upper()
        return EDUCATION_MAP.get(val_str, 0)

    def determine_archetype(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine borrower archetype from user inputs.
        
        Expected features dict keys:
        - NETMONTHLYINCOME
        - AGE
        - Time_With_Curr_Empr
        - EDUCATION
        
        Credit_Score is explicitly NOT expected and should not be used.
        """
        # Exclude Credit_Score explicitly if mistakenly passed
        if 'Credit_Score' in features:
            pass # Just ignore it, or could raise ValueError

        try:
            income = float(features.get('NETMONTHLYINCOME', 0))
            age = float(features.get('AGE', 0))
            tenure = float(features.get('Time_With_Curr_Empr', 0))
            education_raw = features.get('EDUCATION', 'OTHERS')
        except ValueError:
            raise ValueError("Numeric features must be valid numbers.")

        edu_mapped = self._map_education(education_raw)

        # Prepare feature array in the exact order trained: 
        # ['NETMONTHLYINCOME', 'AGE', 'Time_With_Curr_Empr', 'EDUCATION']
        input_data = pd.DataFrame([{
            'NETMONTHLYINCOME': income,
            'AGE': age,
            'Time_With_Curr_Empr': tenure,
            'EDUCATION': edu_mapped
        }])

        # Scale
        X_scaled = self.__class__._cached_scaler.transform(input_data)

        # Predict
        cluster_id = int(self.__class__._cached_model.predict(X_scaled)[0])

        # Get label
        label = self.__class__._cached_definitions.get(cluster_id, "Unknown Archetype")

        return {
            "cluster_id": cluster_id,
            "archetype_label": label
        }

def get_borrower_archetype(features: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function to get the archetype."""
    engine = BorrowerArchetypeEngine()
    return engine.determine_archetype(features)
