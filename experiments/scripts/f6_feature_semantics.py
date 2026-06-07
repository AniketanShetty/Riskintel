import os
import json
import logging
import argparse
import time
import pandas as pd
from utils_manifest import generate_manifest

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Hardcoded Semantic Knowledge Base for common Credit Risk features
SEMANTIC_KB = {
    "cibil_score": {
        "Description": "Credit bureau score",
        "Business Meaning": "Applicant's creditworthiness history",
        "Available Before Decision": "Yes (At Application)",
        "Potential Leakage Risk": "High",
        "Notes": "EXTREME RISK: Bureau scores update dynamically. If this data was pulled recently, it includes the default event of this very loan."
    },
    "annual_income": {
        "Description": "Yearly earnings",
        "Business Meaning": "Capacity to repay",
        "Available Before Decision": "Yes",
        "Potential Leakage Risk": "Low",
        "Notes": "Standard underwriting feature."
    },
    "dependents": {
        "Description": "Number of financial dependents",
        "Business Meaning": "Monthly living expenses proxy",
        "Available Before Decision": "Yes",
        "Potential Leakage Risk": "Low",
        "Notes": "Fair Lending / ECOA Proxy Risk (Familial Status)."
    },
    "education": {
        "Description": "Education level",
        "Business Meaning": "Income stability proxy",
        "Available Before Decision": "Yes",
        "Potential Leakage Risk": "Low",
        "Notes": "Fair Lending / Redlining Proxy Risk."
    },
    "self_employed": {
        "Description": "Employment type flag",
        "Business Meaning": "Income volatility indicator",
        "Available Before Decision": "Yes",
        "Potential Leakage Risk": "Low",
        "Notes": "Standard underwriting feature."
    },
    "loan_amount": {
        "Description": "Requested principal amount",
        "Business Meaning": "Debt burden magnitude",
        "Available Before Decision": "Yes",
        "Potential Leakage Risk": "Low",
        "Notes": "Standard feature."
    },
    "loan_term": {
        "Description": "Duration of loan (months/years)",
        "Business Meaning": "Amortization schedule",
        "Available Before Decision": "Yes",
        "Potential Leakage Risk": "Low",
        "Notes": "Standard feature."
    },
    "residential_assets_value": {
        "Description": "Value of residential property",
        "Business Meaning": "Collateral / Wealth",
        "Available Before Decision": "Yes",
        "Potential Leakage Risk": "Low",
        "Notes": "Requires appraisal verification."
    },
    "commercial_assets_value": {
        "Description": "Value of commercial property",
        "Business Meaning": "Collateral / Wealth",
        "Available Before Decision": "Yes",
        "Potential Leakage Risk": "Low",
        "Notes": "Standard feature."
    },
    "luxury_assets_value": {
        "Description": "Value of luxury assets",
        "Business Meaning": "Liquid or semi-liquid wealth",
        "Available Before Decision": "Yes",
        "Potential Leakage Risk": "Low",
        "Notes": "Standard feature."
    },
    "bank_asset_value": {
        "Description": "Cash reserves in bank",
        "Business Meaning": "Immediate liquidity",
        "Available Before Decision": "Yes",
        "Potential Leakage Risk": "Low",
        "Notes": "Standard feature."
    },
    "loan_status": {
        "Description": "Approval/Default outcome",
        "Business Meaning": "The Target Variable",
        "Available Before Decision": "No",
        "Potential Leakage Risk": "FATAL",
        "Notes": "Must be dropped from X."
    }
}

def analyze_semantics(input_path, base_dir):
    start_time = time.time()
    
    os.makedirs(os.path.join(base_dir, 'metrics'), exist_ok=True)
    os.makedirs(os.path.join(base_dir, 'reports'), exist_ok=True)
    
    logger.info(f"Loading data from {input_path}")
    try:
        df = pd.read_csv(input_path, nrows=5) # Only need headers
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        return

    results = []
    high_risk_count = 0
    
    for col in df.columns:
        norm_col = col.lower().strip()
        kb_entry = SEMANTIC_KB.get(norm_col)
        
        if kb_entry:
            results.append({
                "Feature": col,
                "Description": kb_entry["Description"],
                "Business Meaning": kb_entry["Business Meaning"],
                "Available Before Decision": kb_entry["Available Before Decision"],
                "Potential Leakage Risk": kb_entry["Potential Leakage Risk"],
                "Notes": kb_entry["Notes"]
            })
            if kb_entry["Potential Leakage Risk"] in ["High", "FATAL"]:
                high_risk_count += 1
        else:
            # Check for obvious post-decision keywords
            risk = "Medium (Unknown)"
            if any(word in norm_col for word in ["default", "late", "repay", "recovery", "arrears", "paid", "status"]):
                risk = "High"
                high_risk_count += 1
                
            results.append({
                "Feature": col,
                "Description": "REQUIRES MANUAL AUDIT",
                "Business Meaning": "UNKNOWN",
                "Available Before Decision": "UNKNOWN",
                "Potential Leakage Risk": risk,
                "Notes": "Not in Semantic KB. Must manually verify timestamp of creation."
            })
            
    res_df = pd.DataFrame(results)
    csv_path = os.path.join(base_dir, 'metrics', 'f6_feature_semantics.csv')
    res_df.to_csv(csv_path, index=False)
    logger.info(f"Saved Semantic Audit to {csv_path}")
    
    verdict = "SAFE"
    if high_risk_count > 1: # > 1 because target is usually High/Fatal
        verdict = "HIGH_LEAKAGE_RISK"
    elif high_risk_count == 1 or any(r['Potential Leakage Risk'] == 'Medium (Unknown)' for r in results):
        verdict = "REVIEW_REQUIRED"
        
    logger.info(f"Final Semantic Verdict: {verdict}")
    
    # Save a small JSON verdict
    with open(os.path.join(base_dir, 'metrics', 'f6_feature_semantics_verdict.json'), 'w') as f:
        json.dump({"verdict": verdict, "high_risk_features_count": high_risk_count}, f, indent=4)
        
    generate_manifest(input_path, "f6_feature_semantics", time.time() - start_time, os.path.join(base_dir, 'metrics'))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Feature Semantics Audit")
    parser.add_argument("--input", required=True)
    parser.add_argument("--outdir", default="experiments")
    args = parser.parse_args()
    
    analyze_semantics(args.input, args.outdir)
