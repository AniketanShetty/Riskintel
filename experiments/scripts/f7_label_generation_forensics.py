import os
import json
import logging
import argparse
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

try:
    from utils_manifest import generate_manifest
except ImportError:
    def generate_manifest(*args, **kwargs): pass

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_dirs(base_dir):
    for d in ['metrics', 'plots', 'reports']:
        os.makedirs(os.path.join(base_dir, d), exist_ok=True)

def extract_rules(tree, feature_names):
    tree_rules = export_text(tree, feature_names=list(feature_names))
    return tree_rules

def get_feature_usage(tree, feature_names):
    features_used = []
    for feature_idx in tree.tree_.feature:
        if feature_idx != -2: # Not a leaf node
            features_used.append(feature_names[feature_idx])
    return features_used

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
    
    # Preprocessing
    cat_cols = X.select_dtypes(include=['object', 'category']).columns
    if len(cat_cols) > 0:
        from sklearn.preprocessing import OrdinalEncoder
        oe = OrdinalEncoder()
        X[cat_cols] = oe.fit_transform(X[cat_cols])
        
    X = X.fillna(0)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    metrics_data = []
    feature_counts = {f: 0 for f in X.columns}
    best_tree_d4 = None
    
    depths = [1, 2, 3, 4]
    for depth in depths:
        clf = DecisionTreeClassifier(max_depth=depth, random_state=42)
        clf.fit(X_train, y_train)
        
        preds = clf.predict(X_test)
        probs = clf.predict_proba(X_test)[:, 1]
        
        acc = accuracy_score(y_test, preds)
        prec = precision_score(y_test, preds, zero_division=0)
        rec = recall_score(y_test, preds, zero_division=0)
        f1 = f1_score(y_test, preds, zero_division=0)
        auc = roc_auc_score(y_test, probs)
        
        metrics_data.append({
            'depth': depth,
            'accuracy': acc,
            'precision': prec,
            'recall': rec,
            'f1': f1,
            'roc_auc': auc
        })
        
        if depth == 4:
            best_tree_d4 = clf
            
        used_features = get_feature_usage(clf, X.columns)
        for f in used_features:
            feature_counts[f] += 1
            
    # Save Metrics CSV
    metrics_df = pd.DataFrame(metrics_data)
    metrics_csv_path = os.path.join(base_dir, 'metrics', 'f7_shallow_tree_metrics.csv')
    metrics_df.to_csv(metrics_csv_path, index=False)
    logger.info(f"Saved shallow tree metrics to {metrics_csv_path}")
    
    # Generate Reports: Rules
    rules_text = extract_rules(best_tree_d4, X.columns)
    rules_md_path = os.path.join(base_dir, 'reports', 'f7_decision_rules.md')
    with open(rules_md_path, 'w') as f:
        f.write("# Depth-4 Decision Tree Rules\n\n")
        f.write("```text\n")
        f.write(rules_text)
        f.write("\n```\n")
    logger.info(f"Saved decision rules to {rules_md_path}")
    
    # Save Feature Usage CSV
    usage_df = pd.DataFrame([
        {'feature': k, 'usage_count': v} for k, v in feature_counts.items() if v > 0
    ]).sort_values(by='usage_count', ascending=False)
    
    usage_csv_path = os.path.join(base_dir, 'metrics', 'f7_feature_usage.csv')
    usage_df.to_csv(usage_csv_path, index=False)
    logger.info(f"Saved feature usage to {usage_csv_path}")
    
    # Plot Feature Usage
    plt.figure(figsize=(10, 6))
    if not usage_df.empty:
        plt.bar(usage_df['feature'], usage_df['usage_count'], color='skyblue')
        plt.xticks(rotation=45, ha='right')
        plt.title('Feature Usage Across Shallow Decision Trees (Depths 1-4)')
        plt.ylabel('Split Count')
        plt.tight_layout()
    else:
        plt.text(0.5, 0.5, 'No features used', ha='center', va='center')
        
    plot_path = os.path.join(base_dir, 'plots', 'f7_feature_usage.png')
    plt.savefig(plot_path)
    plt.close()
    
    # Acceptance Criteria & Final Verdict
    d4_auc = metrics_df[metrics_df['depth'] == 4]['roc_auc'].values[0]
    
    if d4_auc < 0.95:
        verdict = "LIKELY_REAL_WORLD_DATA"
        status = "PASS"
        desc = "Depth-4 tree cannot reproduce labels. Data appears behavioral."
    elif d4_auc <= 0.98:
        verdict = "MIXED_SIGNAL"
        status = "WARNING"
        desc = "Depth-4 tree predicts labels strongly. Potential simple rules involved."
    else:
        verdict = "LIKELY_RULE_GENERATED_DATA"
        status = "FAIL"
        desc = "Depth-4 tree almost perfectly reproduces labels. Data is highly likely generated from simple business rules."
        
    verdict_md_path = os.path.join(base_dir, 'reports', 'f7_label_generation_verdict.md')
    with open(verdict_md_path, 'w') as f:
        f.write(f"# Label Generation Forensics Verdict\n\n")
        f.write(f"**Verdict:** {verdict}\n\n")
        f.write(f"**Status:** {status}\n\n")
        f.write(f"**Depth-4 ROC-AUC:** {d4_auc:.4f}\n\n")
        f.write(f"## Interpretation\n{desc}\n")
        
    logger.info(f"Verdict: {verdict} (Status: {status})")
    
    generate_manifest(input_path, "f7_label_generation_forensics", time.time() - start_time, os.path.join(base_dir, 'metrics'))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Label Generation Forensics")
    parser.add_argument("--input", required=True)
    parser.add_argument("--target", required=True, default="loan_status")
    parser.add_argument("--outdir", default="experiments")
    args = parser.parse_args()
    run_experiment(args.input, args.target, args.outdir)
