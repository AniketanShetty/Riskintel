import os
import json
import logging
import argparse
import time
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, roc_curve

from utils_manifest import generate_manifest

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_dirs(base_dir):
    os.makedirs(os.path.join(base_dir, 'metrics'), exist_ok=True)
    os.makedirs(os.path.join(base_dir, 'plots'), exist_ok=True)
    os.makedirs(os.path.join(base_dir, 'reports'), exist_ok=True)

def train_and_evaluate(X_train, X_test, y_train, y_test):
    # Logistic Regression (CIBIL only)
    lr = LogisticRegression(random_state=42, max_iter=1000)
    lr.fit(X_train[['cibil_score']], y_train)
    lr_probs = lr.predict_proba(X_test[['cibil_score']])[:, 1]
    lr_auc = roc_auc_score(y_test, lr_probs)
    
    # Random Forest (CIBIL only)
    rf_cibil = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    rf_cibil.fit(X_train[['cibil_score']], y_train)
    rf_cibil_probs = rf_cibil.predict_proba(X_test[['cibil_score']])[:, 1]
    rf_cibil_auc = roc_auc_score(y_test, rf_cibil_probs)
    
    # Random Forest (Full Model)
    rf_full = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    rf_full.fit(X_train, y_train)
    rf_full_probs = rf_full.predict_proba(X_test)[:, 1]
    rf_full_auc = roc_auc_score(y_test, rf_full_probs)
    
    return {
        'lr_auc': lr_auc, 'lr_probs': lr_probs,
        'rf_cibil_auc': rf_cibil_auc, 'rf_cibil_probs': rf_cibil_probs,
        'rf_full_auc': rf_full_auc, 'rf_full_probs': rf_full_probs
    }

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
    
    # Ordinal encode categorical strings to match full model pipeline
    cat_cols = X.select_dtypes(include=['object', 'category']).columns
    if len(cat_cols) > 0:
        from sklearn.preprocessing import OrdinalEncoder
        oe = OrdinalEncoder()
        X[cat_cols] = oe.fit_transform(X[cat_cols])
        
    X = X.fillna(0)
    
    if 'cibil_score' not in X.columns:
        logger.error("cibil_score feature not found in dataset!")
        return

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    logger.info("Training Single Feature vs Full Models...")
    res = train_and_evaluate(X_train, X_test, y_train, y_test)
    
    lr_cibil_auc = res['lr_auc']
    rf_cibil_auc = res['rf_cibil_auc']
    full_model_auc = res['rf_full_auc']
    delta_vs_full_model = full_model_auc - rf_cibil_auc
    
    status = "PASS"
    if rf_cibil_auc >= 0.97:
        status = "FAIL"
    elif rf_cibil_auc >= 0.90:
        status = "WARNING"
        
    # Save JSON Metrics
    output_json = {
        "lr_cibil_auc": float(lr_cibil_auc),
        "rf_cibil_auc": float(rf_cibil_auc),
        "full_model_auc": float(full_model_auc),
        "delta_vs_full_model": float(delta_vs_full_model),
        "status": status
    }
    
    json_path = os.path.join(base_dir, 'metrics', 'f4_single_feature_auc.json')
    with open(json_path, 'w') as f:
        json.dump(output_json, f, indent=4)
    logger.info(f"Saved metrics to {json_path} (Status: {status})")
    
    # Save ROC Plot
    plt.figure(figsize=(10, 8))
    
    fpr, tpr, _ = roc_curve(y_test, res['lr_probs'])
    plt.plot(fpr, tpr, label=f"LR (CIBIL Only) AUC = {lr_cibil_auc:.4f}", color='blue')
    
    fpr, tpr, _ = roc_curve(y_test, res['rf_cibil_probs'])
    plt.plot(fpr, tpr, label=f"RF (CIBIL Only) AUC = {rf_cibil_auc:.4f}", color='orange')
    
    fpr, tpr, _ = roc_curve(y_test, res['rf_full_probs'])
    plt.plot(fpr, tpr, label=f"RF (Full Model) AUC = {full_model_auc:.4f}", linestyle='--', color='red')
    
    plt.plot([0, 1], [0, 1], 'k--', alpha=0.5)
    plt.title("ROC Curve: Single Feature CIBIL vs Full Model")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.legend(loc="lower right")
    
    plot_path = os.path.join(base_dir, 'plots', 'f4_single_feature_roc.png')
    plt.savefig(plot_path)
    plt.close()
    logger.info(f"Saved plot to {plot_path}")
    
    # Generate reproducible manifest
    execution_duration = time.time() - start_time
    generate_manifest(input_path, "f4_single_feature_auc", execution_duration, os.path.join(base_dir, 'metrics'))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Single Feature AUC Experiment")
    parser.add_argument("--input", required=True)
    parser.add_argument("--target", required=True, default="loan_status")
    parser.add_argument("--outdir", default="experiments")
    args = parser.parse_args()
    
    run_experiment(args.input, args.target, args.outdir)
