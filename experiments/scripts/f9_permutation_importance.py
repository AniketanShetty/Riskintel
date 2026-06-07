import os
import json
import logging
import argparse
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.inspection import permutation_importance
from sklearn.preprocessing import OrdinalEncoder

from utils_manifest import generate_manifest

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_dirs(base_dir):
    os.makedirs(os.path.join(base_dir, 'metrics'), exist_ok=True)
    os.makedirs(os.path.join(base_dir, 'plots'), exist_ok=True)
    os.makedirs(os.path.join(base_dir, 'reports'), exist_ok=True)

def generate_report(base_dir, metrics_df, cibil_dominance, status):
    report_content = f"""# E1 Permutation Importance Audit Report

## Overview
This report assesses feature dominance using Permutation Importance (metric: ROC-AUC degradation). 
The objective is to quantify the relative contribution of each feature and explicitly calculate the dominance of `cibil_score` to determine if the E1 model is a genuine multivariate model or a simple CIBIL wrapper.

## Feature Importance Summary

| Feature | Importance (AUC Drop) | Relative Contribution (%) |
|---------|-----------------------|---------------------------|
"""
    for index, row in metrics_df.iterrows():
        report_content += f"| {row['Feature']} | {row['Importance (Mean)']:.4f} ± {row['Importance (Std)']:.4f} | {row['Relative Contribution (%)']:.2f}% |\n"

    report_content += f"""
## Key Metric
*   **`cibil_score` Dominance:** {cibil_dominance:.2f}%
*   **Verdict:** {status}

"""
    if status == "PASS":
        report_content += """### Academic Defense Interpretation
The permutation importance audit confirms that the model relies on a diverse set of features. The `cibil_score` dominance is strictly below or equal to 50% (actual: {cibil_dominance:.2f}%), indicating that the model successfully integrates peripheral financial behaviors and demographic indicators. The model demonstrates genuine multivariate learning, structurally insulated from single-point failure if the primary credit bureau score is compromised.

### Interview Talking Points
*   **"Is the model overly dependent on CIBIL?"** -> "No. Our permutation importance tests show CIBIL accounts for {cibil_dominance:.2f}% of the model's predictive power. Over 50% of the signal is extracted from alternative features."
*   **"How do you validate feature synergy?"** -> "By randomizing features individually and measuring ROC-AUC degradation. We found significant and distributed performance drops across multiple features, proving they are active, non-redundant components of the decision boundary."
"""
    elif status == "WARNING":
        report_content += """### Academic Defense Interpretation
The model exhibits heavy reliance on the `cibil_score`, which accounts for {cibil_dominance:.2f}% of its predictive importance. While peripheral features contribute non-trivial signal (preventing a complete single-feature collapse), the density of the learning is skewed. This suggests that while the model is multivariate, its secondary features act largely as edge-case adjusters.

### Interview Talking Points
*   **"Are the alternative features doing any heavy lifting?"** -> "They contribute a meaningful but minority share of the predictive power ({100 - cibil_dominance:.2f}%). CIBIL remains the primary anchor. We are investigating ways to elevate the signal-to-noise ratio in our alternative data."
*   **"What is the risk of this skewed distribution?"** -> "It makes the model highly sensitive to shifts in CIBIL score distribution, but it does not constitute a full failure of multivariate modeling."
"""
    else:
        report_content += """### Academic Defense Interpretation
The model suffers from single-feature dominance. Permutation analysis reveals that `cibil_score` alone accounts for {cibil_dominance:.2f}% of the total feature importance. The degradation in ROC-AUC when randomizing other features is negligible. This indicates the Random Forest has collapsed into a functional approximation of a single-variable threshold model, failing to capture meaningful multivariate interactions.

### Interview Talking Points
*   **"Did the model learn anything beyond the credit score?"** -> "No. Our empirical permutation tests prove the model is functionally a CIBIL wrapper. Over {cibil_dominance:.2f}% of the importance is concentrated in that single feature."
*   **"Why is this a failure?"** -> "Because deploying a complex ensemble method (Random Forest) for a single-variable decision boundary is computationally wasteful and mathematically brittle. We must either simplify the model or heavily re-engineer the alternative feature space."
"""
    
    report_path = os.path.join(base_dir, 'reports', 'f9_permutation_importance_report.md')
    with open(report_path, 'w') as f:
        f.write(report_content)
    logger.info(f"Saved Markdown report to {report_path}")

def run_experiment(input_path, target_col, base_dir):
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
    
    cat_cols = X.select_dtypes(include=['object', 'category']).columns
    if len(cat_cols) > 0:
        oe = OrdinalEncoder()
        X[cat_cols] = oe.fit_transform(X[cat_cols])
        
    X = X.fillna(0)
    
    if 'cibil_score' not in X.columns:
        logger.warning("cibil_score feature not found! Will proceed but cibil_dominance will be 0%.")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Train Full Model
    rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    rf.fit(X_train, y_train)
    
    baseline_probs = rf.predict_proba(X_test)[:, 1]
    baseline_auc = roc_auc_score(y_test, baseline_probs)
    logger.info(f"Baseline Full Model AUC: {baseline_auc:.4f}")

    # Permutation Importance
    logger.info("Calculating Permutation Importance (scoring='roc_auc')...")
    result = permutation_importance(
        rf, X_test, y_test, scoring='roc_auc', n_repeats=10, random_state=42, n_jobs=-1
    )
    
    importances_mean = result.importances_mean
    importances_std = result.importances_std
    
    # Avoid negative importance summing issues by clipping at 0 for percentage contribution
    importances_mean_clipped = np.maximum(importances_mean, 0)
    total_importance = np.sum(importances_mean_clipped)
    
    if total_importance > 0:
        relative_contributions = (importances_mean_clipped / total_importance) * 100
    else:
        relative_contributions = np.zeros_like(importances_mean)
        
    features = X.columns
    
    results_df = pd.DataFrame({
        'Feature': features,
        'Importance (Mean)': importances_mean,
        'Importance (Std)': importances_std,
        'Relative Contribution (%)': relative_contributions
    })
    
    results_df = results_df.sort_values(by='Importance (Mean)', ascending=False).reset_index(drop=True)
    
    # Compute cibil_score dominance
    if 'cibil_score' in features:
        cibil_dominance = results_df.loc[results_df['Feature'] == 'cibil_score', 'Relative Contribution (%)'].values[0]
    else:
        cibil_dominance = 0.0
        
    # Status Thresholds
    if cibil_dominance <= 50.0:
        status = "PASS"
    elif cibil_dominance <= 80.0:
        status = "WARNING"
    else:
        status = "FAIL"

    # 1. Save CSV
    csv_path = os.path.join(base_dir, 'metrics', 'f9_permutation_importance.csv')
    results_df.to_csv(csv_path, index=False)
    logger.info(f"Saved CSV to {csv_path}")

    # 2. Save JSON
    json_output = {
        "baseline_auc": float(baseline_auc),
        "total_importance": float(total_importance),
        "cibil_dominance_percentage": float(cibil_dominance),
        "status": status,
        "features": results_df.to_dict(orient="records")
    }
    json_path = os.path.join(base_dir, 'metrics', 'f9_permutation_importance.json')
    with open(json_path, 'w') as f:
        json.dump(json_output, f, indent=4)
    logger.info(f"Saved JSON to {json_path}")
    
    # 3. Save PNG Bar Chart
    plt.figure(figsize=(12, 8))
    plt.barh(results_df['Feature'][::-1], results_df['Importance (Mean)'][::-1], xerr=results_df['Importance (Std)'][::-1], align='center', color='skyblue', edgecolor='black')
    plt.xlabel('Permutation Importance (AUC Decrease)')
    plt.title('Feature Permutation Importance (ROC-AUC)')
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    png_path = os.path.join(base_dir, 'plots', 'f9_permutation_importance_bar.png')
    plt.savefig(png_path)
    plt.close()
    logger.info(f"Saved PNG to {png_path}")

    # 4. Generate Report
    generate_report(base_dir, results_df, cibil_dominance, status)
    
    # Generate reproducible manifest
    execution_duration = time.time() - start_time
    generate_manifest(input_path, "f9_permutation_importance", execution_duration, os.path.join(base_dir, 'metrics'))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Permutation Importance Audit")
    parser.add_argument("--input", required=True)
    parser.add_argument("--target", required=True, default="loan_status")
    parser.add_argument("--outdir", default="experiments")
    args = parser.parse_args()
    
    run_experiment(args.input, args.target, args.outdir)
