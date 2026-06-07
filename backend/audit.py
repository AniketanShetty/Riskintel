import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

def eval_model(model, X_test, y_test):
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    return {
        "Accuracy": accuracy_score(y_test, y_pred),
        "Precision": precision_score(y_test, y_pred),
        "Recall": recall_score(y_test, y_pred),
        "F1": f1_score(y_test, y_pred),
        "ROC-AUC": roc_auc_score(y_test, y_prob)
    }

def run_audit():
    df = pd.read_csv('data/processed/eligibility_data.csv')
    X = df.drop(columns=['loan_status'])
    y = df['loan_status']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # 1. Full Model
    rf_full = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    rf_full.fit(X_train, y_train)
    metrics_full = eval_model(rf_full, X_test, y_test)

    # 2. Baseline Model (cibil_score only)
    X_train_base = X_train[['cibil_score']]
    X_test_base = X_test[['cibil_score']]
    rf_base = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    rf_base.fit(X_train_base, y_train)
    metrics_base = eval_model(rf_base, X_test_base, y_test)

    # Feature Importances
    importances = pd.Series(rf_full.feature_importances_, index=X.columns).sort_values(ascending=False)

    md_content = f"""# Eligibility Engine Audit

## 1. Metrics Comparison

| Metric | Full Random Forest | Baseline (CIBIL Only) | Difference |
|---|---|---|---|
| Accuracy | {metrics_full['Accuracy']:.4f} | {metrics_base['Accuracy']:.4f} | {metrics_full['Accuracy'] - metrics_base['Accuracy']:+.4f} |
| Precision | {metrics_full['Precision']:.4f} | {metrics_base['Precision']:.4f} | {metrics_full['Precision'] - metrics_base['Precision']:+.4f} |
| Recall | {metrics_full['Recall']:.4f} | {metrics_base['Recall']:.4f} | {metrics_full['Recall'] - metrics_base['Recall']:+.4f} |
| F1-Score | {metrics_full['F1']:.4f} | {metrics_base['F1']:.4f} | {metrics_full['F1'] - metrics_base['F1']:+.4f} |
| ROC-AUC | {metrics_full['ROC-AUC']:.4f} | {metrics_base['ROC-AUC']:.4f} | {metrics_full['ROC-AUC'] - metrics_base['ROC-AUC']:+.4f} |

## 2. Feature Importances (Full Model)

"""
    for feat, imp in importances.items():
        md_content += f"- **{feat}**: {imp:.4f}\n"

    md_content += """
## 3. Target Leakage Analysis
"""
    if importances['cibil_score'] > 0.8 and metrics_base['Accuracy'] > 0.95:
        md_content += "⚠️ **High Risk of Target Leakage Detected:** The `cibil_score` feature alone achieves near-perfect classification performance and absolutely dominates the feature importance. This strongly suggests that in this synthetic dataset, `cibil_score` was used almost deterministically to derive the `loan_status` label (e.g., hard cutoff rule). In a real-world scenario, predicting approval solely based on CIBIL makes the rest of the engine redundant.\n"
    elif importances['cibil_score'] > 0.5:
        md_content += "⚠️ **Moderate Risk of Target Leakage:** `cibil_score` is overwhelmingly the strongest predictor. While some variance exists, this feature acts as a dominant heuristic for the target variable.\n"
    else:
        md_content += "✅ No obvious single-feature deterministic leakage found. Feature importance is reasonably distributed.\n"

    os.makedirs(os.path.join("..", "docs"), exist_ok=True)
    with open('../docs/model_audit.md', 'w', encoding='utf-8') as f:
        f.write(md_content)

    print(md_content)

if __name__ == "__main__":
    run_audit()
