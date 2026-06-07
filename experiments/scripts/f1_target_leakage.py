import os
import json
import logging
import argparse
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import pointbiserialr
from sklearn.feature_selection import mutual_info_classif
from sklearn.preprocessing import OrdinalEncoder
import time
from utils_manifest import generate_manifest

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_dirs(base_dir):
    os.makedirs(os.path.join(base_dir, 'metrics'), exist_ok=True)
    os.makedirs(os.path.join(base_dir, 'plots'), exist_ok=True)

def calculate_leakage(input_path, target_col, base_dir):
    start_time = time.time()
    setup_dirs(base_dir)
    logger.info(f"Loading data from {input_path}")
    
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        return

    if target_col not in df.columns:
        logger.error(f"Target column '{target_col}' not found.")
        return

    X = df.drop(columns=[target_col])
    y = df[target_col]

    # Handle categoricals for MI
    cat_cols = X.select_dtypes(include=['object', 'category']).columns
    if len(cat_cols) > 0:
        oe = OrdinalEncoder()
        X[cat_cols] = oe.fit_transform(X[cat_cols])
    
    X = X.fillna(0) # Basic imputation for missing values if any

    results = []
    max_corr = 0
    max_corr_feat = None
    max_mi = 0
    max_mi_feat = None

    logger.info("Calculating Mutual Information...")
    mi_scores = mutual_info_classif(X, y, random_state=42)

    logger.info("Calculating Point-Biserial Correlations...")
    for idx, col in enumerate(X.columns):
        # Point-biserial only valid for continuous vs binary
        try:
            pb_corr, _ = pointbiserialr(X[col], y)
            pb_corr = abs(pb_corr) if not pd.isna(pb_corr) else 0.0
        except Exception:
            pb_corr = 0.0
        
        mi = mi_scores[idx]
        
        if pb_corr > max_corr:
            max_corr = pb_corr
            max_corr_feat = col
            
        if mi > max_mi:
            max_mi = mi
            max_mi_feat = col

        results.append({
            'feature': col,
            'point_biserial_corr': pb_corr,
            'mi_score': mi
        })

    # Save CSV
    results_df = pd.DataFrame(results)
    csv_out = os.path.join(base_dir, 'metrics', 'f1_leakage_scores.csv')
    results_df.to_csv(csv_out, index=False)
    logger.info(f"Saved CSV to {csv_out}")

    # Save JSON
    summary = {
        'max_corr_feature': max_corr_feat,
        'max_corr_value': max_corr,
        'max_mi_feature': max_mi_feat,
        'max_mi_value': max_mi
    }
    json_out = os.path.join(base_dir, 'metrics', 'f1_leakage_summary.json')
    with open(json_out, 'w') as f:
        json.dump(summary, f, indent=4)
    logger.info(f"Saved JSON to {json_out}")

    # Save PNG
    if max_corr_feat:
        plt.figure(figsize=(10, 6))
        sns.kdeplot(data=df, x=max_corr_feat, hue=target_col, fill=True, common_norm=False)
        plt.title(f"Target Leakage KDE: {max_corr_feat} vs {target_col}")
        png_out = os.path.join(base_dir, 'plots', 'f1_leakage_kde.png')
        plt.savefig(png_out)
        plt.close()
        logger.info(f"Saved Plot to {png_out}")

    # Generate Manifest
    execution_duration = time.time() - start_time
    generate_manifest(
        dataset_path=input_path,
        script_name="f1_target_leakage",
        execution_duration_seconds=execution_duration,
        output_dir=os.path.join(base_dir, 'metrics')
    )
    logger.info("Saved Run Manifest.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Target Leakage Detection")
    parser.add_argument("--input", required=True, help="Path to input CSV")
    parser.add_argument("--target", required=True, help="Target column name")
    parser.add_argument("--outdir", default="experiments", help="Base output directory")
    args = parser.parse_args()
    
    calculate_leakage(args.input, args.target, args.outdir)
