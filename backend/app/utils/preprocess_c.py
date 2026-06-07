import os
import json
import pandas as pd
from validation import setup_logger

logger = setup_logger("preprocess_c")

def extract_risk_tier_thresholds(input_path: str, thresholds_out: str) -> None:
    logger.info(f"Loading Dataset C from {input_path} to extract risk thresholds...")
    df = pd.read_csv(input_path)
    
    if "Approved_Flag" not in df.columns or "Credit_Score" not in df.columns:
        raise ValueError("Missing required columns: Approved_Flag or Credit_Score in Dataset C.")
        
    logger.info("Calculating Credit_Score boundaries for Risk Tiers...")
    
    p1_scores = df[df["Approved_Flag"] == "P1"]["Credit_Score"].dropna()
    p2_scores = df[df["Approved_Flag"] == "P2"]["Credit_Score"].dropna()
    p4_scores = df[df["Approved_Flag"] == "P4"]["Credit_Score"].dropna()
    
    p1_min = int(p1_scores.min()) if not p1_scores.empty else 701
    p2_min = int(p2_scores.min()) if not p2_scores.empty else 669
    p4_max = int(p4_scores.max()) if not p4_scores.empty else 658

    threshold_config = {
        "P1": {
            "condition": f">= {p1_min}",
            "min_score": p1_min
        },
        "P2": {
            "condition": f">= {p2_min} and < {p1_min}",
            "min_score": p2_min,
            "max_score": p1_min - 1
        },
        "P4": {
            "condition": f"<= {p4_max}",
            "max_score": p4_max
        },
        "P3": {
            "condition": "fallback",
            "description": "Default assignment for any score that does not strictly satisfy P1, P2, or P4 explicit thresholds."
        }
    }
        
    logger.info(f"Extracted robust threshold config: {json.dumps(threshold_config, indent=2)}")
    
    os.makedirs(os.path.dirname(thresholds_out), exist_ok=True)
    with open(thresholds_out, 'w') as f:
        json.dump(threshold_config, f, indent=4)
        
    logger.info(f"Saved risk tier thresholds to {thresholds_out}")

if __name__ == "__main__":
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    INPUT_FILE = os.path.join(PROJECT_ROOT, "data", "raw", "External_Cibil_Dataset.csv")
    THRESHOLDS_OUT1 = os.path.join(PROJECT_ROOT, "data", "processed", "risk_tier_thresholds.json")
    THRESHOLDS_OUT2 = os.path.join(PROJECT_ROOT, "models", "risk_tier", "risk_tier_thresholds.json")
    
    extract_risk_tier_thresholds(INPUT_FILE, THRESHOLDS_OUT1)
    
    os.makedirs(os.path.dirname(THRESHOLDS_OUT2), exist_ok=True)
    import shutil
    shutil.copy2(THRESHOLDS_OUT1, THRESHOLDS_OUT2)
    logger.info(f"Copied thresholds to {THRESHOLDS_OUT2}")
