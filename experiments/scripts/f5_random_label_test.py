import os
import json
import logging
import argparse
import time
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from utils_manifest import generate_manifest

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_dirs(base_dir):
    os.makedirs(os.path.join(base_dir, 'metrics'), exist_ok=True)
    os.makedirs(os.path.join(base_dir, 'plots'), exist_ok=True)
    os.makedirs(os.path.join(base_dir, 'reports'), exist_ok=True)

def run_experiment(input_path, target_col, base_dir, iterations=5):
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
    y_true = df[target_col].copy()
    
    # Ordinal encode categorical strings
    cat_cols = X.select_dtypes(include=['object', 'category']).columns
    if len(cat_cols) > 0:
        from sklearn.preprocessing import OrdinalEncoder
        oe = OrdinalEncoder()
        X[cat_cols] = oe.fit_transform(X[cat_cols])
        
    X = X.fillna(0)
    
    auc_scores = []
    
    logger.info(f"Running {iterations} iterations of Random Label Test...")
    for i in range(iterations):
        # 1. Randomly shuffle the target labels (Y-Randomization)
        # This mathematically destroys any real signal. Expected AUC = 0.5
        np.random.seed(42 + i)
        y_shuffled = np.random.permutation(y_true)
        
        # 2. Train/Test split
        X_train, X_test, y_train, y_test = train_test_split(X, y_shuffled, test_size=0.2, random_state=42 + i)
        
        # 3. Retrain exact E1 RF architecture
        rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42 + i)
        rf.fit(X_train, y_train)
        
        # 4. Evaluate
        probs = rf.predict_proba(X_test)[:, 1]
        
        # Handle cases where shuffling creates only 1 class in test set
        if len(np.unique(y_test)) > 1:
            auc = roc_auc_score(y_test, probs)
            auc_scores.append(auc)
            logger.info(f"Iteration {i+1} AUC: {auc:.4f}")
        else:
            logger.warning(f"Iteration {i+1} skipped (only 1 class in test set)")
            
    if not auc_scores:
        logger.error("No valid iterations completed.")
        return

    mean_auc = np.mean(auc_scores)
    
    status = "PASS"
    if mean_auc > 0.60:
        status = "FAIL"
    elif not (0.45 <= mean_auc <= 0.55):
        status = "WARNING"
        
    # Save JSON Metrics
    output_json = {
        "random_label_auc": float(mean_auc),
        "status": status,
        "iterations": len(auc_scores),
        "auc_scores": [float(a) for a in auc_scores]
    }
    
    json_path = os.path.join(base_dir, 'metrics', 'f5_random_label_auc.json')
    with open(json_path, 'w') as f:
        json.dump(output_json, f, indent=4)
    logger.info(f"Saved metrics to {json_path} (Status: {status})")
    
    # Save Plot
    plt.figure(figsize=(8, 6))
    if len(auc_scores) > 1:
        sns.histplot(auc_scores, bins=10, kde=True, color='purple')
    else:
        plt.bar(["AUC"], auc_scores, color='purple')
        
    plt.axvline(0.5, color='black', linestyle='--', label='Expected Random AUC (0.5)')
    plt.axvline(mean_auc, color='red', linestyle='-', label=f'Mean AUC ({mean_auc:.4f})')
    plt.title("Distribution of AUCs on Shuffled Labels")
    plt.xlabel("ROC-AUC Score")
    plt.ylabel("Frequency")
    plt.legend()
    
    plot_path = os.path.join(base_dir, 'plots', 'f5_random_label_distribution.png')
    plt.savefig(plot_path)
    plt.close()
    logger.info(f"Saved plot to {plot_path}")
    
    # Manifest
    execution_duration = time.time() - start_time
    generate_manifest(input_path, "f5_random_label_test", execution_duration, os.path.join(base_dir, 'metrics'))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Random Label Test")
    parser.add_argument("--input", required=True)
    parser.add_argument("--target", required=True, default="loan_status")
    parser.add_argument("--outdir", default="experiments")
    parser.add_argument("--iterations", type=int, default=5)
    args = parser.parse_args()
    
    run_experiment(args.input, args.target, args.outdir, args.iterations)
