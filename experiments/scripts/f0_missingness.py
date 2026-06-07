import os
import json
import logging
import argparse
import time
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from utils_manifest import generate_manifest

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_dirs(base_dir):
    os.makedirs(os.path.join(base_dir, 'metrics'), exist_ok=True)
    os.makedirs(os.path.join(base_dir, 'plots'), exist_ok=True)

def analyze_missingness(input_path, base_dir):
    start_time = time.time()
    setup_dirs(base_dir)
    logger.info(f"Loading data from {input_path}")
    
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        return
        
    total_rows = len(df)
    results = []
    summary = {
        "total_columns": len(df.columns),
        "empty_columns": 0,
        "near_empty_columns": 0,
        "constant_columns": 0
    }
    
    for col in df.columns:
        missing_count = int(df[col].isnull().sum())
        missing_pct = missing_count / total_rows if total_rows > 0 else 0
        unique_count = int(df[col].nunique(dropna=True))
        cardinality_ratio = unique_count / total_rows if total_rows > 0 else 0
        
        status = "PASS"
        if missing_pct == 1.0:
            status = "FAIL"
            summary["empty_columns"] += 1
        elif missing_pct > 0.5:
            status = "FAIL"
            summary["near_empty_columns"] += 1
        elif missing_pct > 0.05:
            status = "WARNING"
            
        if unique_count <= 1 and missing_pct < 1.0:
            summary["constant_columns"] += 1
            status = "FAIL"
            
        results.append({
            "feature": col,
            "missing_count": missing_count,
            "missing_pct": round(missing_pct, 4),
            "unique_count": unique_count,
            "cardinality_ratio": round(cardinality_ratio, 4),
            "status": status
        })
        
    # Save Outputs
    pd.DataFrame(results).to_csv(os.path.join(base_dir, 'metrics', 'f0_missingness.csv'), index=False)
    
    with open(os.path.join(base_dir, 'metrics', 'f0_missingness_summary.json'), 'w') as f:
        json.dump(summary, f, indent=4)
        
    # Plotting
    plt.figure(figsize=(12, 8))
    sns.heatmap(df.isnull(), cbar=False, cmap='viridis', yticklabels=False)
    plt.title("Dataset Missingness Heatmap (Yellow = Missing)")
    plt.tight_layout()
    plt.savefig(os.path.join(base_dir, 'plots', 'f0_missingness_heatmap.png'))
    plt.close()
    
    # Manifest
    generate_manifest(input_path, "f0_missingness", time.time() - start_time, os.path.join(base_dir, 'metrics'))
    logger.info("Missingness analysis complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Missingness Audit")
    parser.add_argument("--input", required=True)
    parser.add_argument("--outdir", default="experiments")
    args = parser.parse_args()
    analyze_missingness(args.input, args.outdir)
