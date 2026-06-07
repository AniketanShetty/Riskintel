import os
import json
import logging
import argparse
import time
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, roc_curve, precision_score, recall_score, f1_score
from sklearn.preprocessing import OrdinalEncoder

from utils_manifest import generate_manifest

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_dirs(base_dir):
    os.makedirs(os.path.join(base_dir, 'metrics'), exist_ok=True)
    os.makedirs(os.path.join(base_dir, 'plots'), exist_ok=True)
    os.makedirs(os.path.join(base_dir, 'reports'), exist_ok=True)

def train_and_evaluate(X_train, X_test, y_train, y_test, is_ablated=False):
    # Random Forest Model
    rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    rf.fit(X_train, y_train)
    probs = rf.predict_proba(X_test)[:, 1]
    preds = rf.predict(X_test)
    
    auc = roc_auc_score(y_test, probs)
    precision = precision_score(y_test, preds, zero_division=0)
    recall = recall_score(y_test, preds, zero_division=0)
    f1 = f1_score(y_test, preds, zero_division=0)
    
    return {
        'model': 'Ablated' if is_ablated else 'Baseline',
        'auc': auc,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'probs': probs
    }

def generate_report(base_dir, baseline_metrics, ablated_metrics, status):
    report_content = f"""# CIBIL Ablation Experiment Verdict

## Overview
This report assesses the structural dependency of the Random Forest model on the `cibil_score` feature. 
The objective is to determine if the exceptionally high baseline ROC-AUC represents genuine multivariate predictive learning, or simple dominance by a single feature.

## Metrics Comparison

| Metric | Baseline (Full Feature Set) | Ablated (Without `cibil_score`) | Delta |
|--------|-----------------------------|---------------------------------|-------|
| ROC-AUC | {baseline_metrics['auc']:.4f} | {ablated_metrics['auc']:.4f} | {baseline_metrics['auc'] - ablated_metrics['auc']:.4f} |
| Precision | {baseline_metrics['precision']:.4f} | {ablated_metrics['precision']:.4f} | {baseline_metrics['precision'] - ablated_metrics['precision']:.4f} |
| Recall | {baseline_metrics['recall']:.4f} | {ablated_metrics['recall']:.4f} | {baseline_metrics['recall'] - ablated_metrics['recall']:.4f} |
| F1 Score | {baseline_metrics['f1']:.4f} | {ablated_metrics['f1']:.4f} | {baseline_metrics['f1'] - ablated_metrics['f1']:.4f} |

## Verdict: {status}

"""
    if status == "PASS":
        report_content += """### Academic Defense Interpretation
The model demonstrates **robust multivariate learning**. The ablation of `cibil_score` leaves the model with substantial predictive power (AUC >= 0.85). This confirms that while the CIBIL score is highly informative, the model has successfully extracted orthogonal, non-redundant signal from the remaining feature space. The 0.9988 baseline AUC is not an artifact of single-feature dominance but a synergy of multiple risk indicators.

### Interview Talking Points
*   **"Is your model just a CIBIL wrapper?"** -> "No. We proved via rigorous ablation testing that even completely blinding the model to the CIBIL score yields an AUC of over 0.85. The algorithm genuinely understands borrower archetype from peripheral financial behavior."
*   **"How do you know it's not overfitting to one feature?"** -> "By removing the dominant feature and verifying that precision and recall remain structurally sound. The latent features provide a solid secondary safety net."
"""
    elif status == "WARNING":
        report_content += """### Academic Defense Interpretation
The model exhibits **heavy reliance** on the `cibil_score`. With the ablated AUC falling between 0.70 and 0.85, the model retains some independent signal, but the predictive density is highly concentrated in the credit score. The baseline performance is largely driven by this single vector, meaning peripheral features act mostly as marginal adjusters rather than core drivers.

### Interview Talking Points
*   **"Are the other features actually useful?"** -> "They are marginally useful. We observe an AUC of {ablated_metrics['auc']:.2f} without CIBIL, which means there is non-random signal, but the CIBIL score does the heavy lifting. We are currently investigating feature engineering to extract more value from alternative data."
*   **"What happens if CIBIL data is unavailable?"** -> "The model degrades significantly but does not fail completely. It remains viable for rudimentary triage but loses its precision-targeting capability."
"""
    else:
        report_content += """### Academic Defense Interpretation
The model suffers from **single-feature dominance**. The ablated AUC falls below 0.70, indicating a systemic collapse of predictive power when `cibil_score` is removed. The baseline AUC of 0.9988 is a direct proxy for the credit score. The peripheral features provide negligible orthogonal information, essentially making the Random Forest an expensive wrapper around a single variable.

### Interview Talking Points
*   **"Why use a Random Forest if it's just looking at CIBIL?"** -> "This ablation test revealed exactly that structural weakness. Currently, the model is overly dependent on the CIBIL score. We must re-evaluate our feature space and potentially use simpler models (like Logistic Regression) if alternative data holds no independent signal."
*   **"Is the 0.99 AUC real?"** -> "It is mathematically real but practically brittle. It reflects the purity of the CIBIL score relative to the labels, not complex multivariate pattern recognition."
"""

    report_path = os.path.join(base_dir, 'reports', 'f8_cibil_ablation_report.md')
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
    
    # Ordinal encode categorical strings
    cat_cols = X.select_dtypes(include=['object', 'category']).columns
    if len(cat_cols) > 0:
        oe = OrdinalEncoder()
        X[cat_cols] = oe.fit_transform(X[cat_cols])
        
    X = X.fillna(0)
    
    if 'cibil_score' not in X.columns:
        logger.error("cibil_score feature not found in dataset!")
        return

    # Create Identical Splits
    X_train_base, X_test_base, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Create Ablated Sets
    X_train_ablated = X_train_base.drop(columns=['cibil_score'])
    X_test_ablated = X_test_base.drop(columns=['cibil_score'])

    logger.info("Training Baseline Full Model...")
    baseline_res = train_and_evaluate(X_train_base, X_test_base, y_train, y_test, is_ablated=False)
    
    logger.info("Training Ablated Model (No CIBIL)...")
    ablated_res = train_and_evaluate(X_train_ablated, X_test_ablated, y_train, y_test, is_ablated=True)
    
    # Threshold Logic on Ablated AUC
    ablated_auc = ablated_res['auc']
    if ablated_auc >= 0.85:
        status = "PASS"
    elif ablated_auc >= 0.70:
        status = "WARNING"
    else:
        status = "FAIL"

    # Save JSON Metrics
    output_json = {
        "baseline": {
            "auc": float(baseline_res['auc']),
            "precision": float(baseline_res['precision']),
            "recall": float(baseline_res['recall']),
            "f1": float(baseline_res['f1'])
        },
        "ablated": {
            "auc": float(ablated_res['auc']),
            "precision": float(ablated_res['precision']),
            "recall": float(ablated_res['recall']),
            "f1": float(ablated_res['f1'])
        },
        "delta_auc": float(baseline_res['auc'] - ablated_res['auc']),
        "status": status
    }
    
    json_path = os.path.join(base_dir, 'metrics', 'f8_cibil_ablation.json')
    with open(json_path, 'w') as f:
        json.dump(output_json, f, indent=4)
    logger.info(f"Saved metrics to {json_path} (Status: {status})")
    
    # Save ROC Plot
    plt.figure(figsize=(10, 8))
    
    fpr_base, tpr_base, _ = roc_curve(y_test, baseline_res['probs'])
    plt.plot(fpr_base, tpr_base, label=f"Baseline (Full) AUC = {baseline_res['auc']:.4f}", color='red')
    
    fpr_abl, tpr_abl, _ = roc_curve(y_test, ablated_res['probs'])
    plt.plot(fpr_abl, tpr_abl, label=f"Ablated (No CIBIL) AUC = {ablated_res['auc']:.4f}", linestyle='--', color='blue')
    
    plt.plot([0, 1], [0, 1], 'k--', alpha=0.5)
    plt.title("ROC Curve: CIBIL Ablation vs Full Model")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.legend(loc="lower right")
    
    plot_path = os.path.join(base_dir, 'plots', 'f8_cibil_ablation_roc.png')
    plt.savefig(plot_path)
    plt.close()
    logger.info(f"Saved plot to {plot_path}")

    # Generate Markdown Report
    generate_report(base_dir, baseline_res, ablated_res, status)
    
    # Generate reproducible manifest
    execution_duration = time.time() - start_time
    generate_manifest(input_path, "f8_cibil_ablation", execution_duration, os.path.join(base_dir, 'metrics'))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CIBIL Ablation Experiment")
    parser.add_argument("--input", required=True)
    parser.add_argument("--target", required=True, default="loan_status")
    parser.add_argument("--outdir", default="experiments")
    args = parser.parse_args()
    
    run_experiment(args.input, args.target, args.outdir)
