import os
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

import sys
# Polyfill for distutils to fix treeinterpreter on Python 3.12+
if 'distutils' not in sys.modules:
    import types
    distutils = types.ModuleType('distutils')
    distutils.version = types.ModuleType('distutils.version')
    class LooseVersion:
        def __init__(self, v): self.v = str(v)
        def __lt__(self, other): return self.v < str(other.v)
        def __ge__(self, other): return self.v >= str(other.v)
    distutils.version.LooseVersion = LooseVersion
    sys.modules['distutils'] = distutils
    sys.modules['distutils.version'] = distutils.version

from treeinterpreter import treeinterpreter as ti

def main():
    # 1. Paths
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
    DATA_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "eligibility_data.csv")
    MODEL_DIR = os.path.join(PROJECT_ROOT, "models", "eligibility")
    MODEL_PATH = os.path.join(MODEL_DIR, "random_forest.joblib")
    
    os.makedirs(MODEL_DIR, exist_ok=True)

    print(f"Loading data from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    
    # 2. Split Features & Target
    X = df.drop(columns=["loan_status"])
    y = df["loan_status"]
    
    print(f"Dataset shape: {df.shape}")
    print(f"Target distribution:\n{y.value_counts(normalize=True)}")

    # 3. Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"\nTrain shape: {X_train.shape}, Test shape: {X_test.shape}")

    # 4. Train Model
    print("\nTraining Random Forest Classifier...")
    model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    model.fit(X_train, y_train)

    # 5. Evaluate
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    print("\n=== Evaluation Metrics (Test Set) ===")
    print(f"Accuracy:  {accuracy_score(y_test, y_pred):.4f}")
    print(f"Precision: {precision_score(y_test, y_pred):.4f}")
    print(f"Recall:    {recall_score(y_test, y_pred):.4f}")
    print(f"F1-Score:  {f1_score(y_test, y_pred):.4f}")
    print(f"ROC-AUC:   {roc_auc_score(y_test, y_prob):.4f}")

    # 6. Local Explainability (treeinterpreter)
    print("\n=== Local Explainability (Sample 0) ===")
    sample = X_test.iloc[[0]]
    prediction, bias, contributions = ti.predict(model, sample)
    
    # prediction returns probabilities for all classes. We want the positive class (idx 1).
    pos_idx = 1
    
    pred_prob = prediction[0][pos_idx]
    base_bias = bias[0][pos_idx]
    
    print(f"Predicted Probability (Class 1): {pred_prob:.4f}")
    print(f"Base Bias:                       {base_bias:.4f}")
    print("\nFeature Contributions:")
    
    feature_names = X_test.columns
    total_contrib = 0.0
    
    for i, feature in enumerate(feature_names):
        val = sample.iloc[0][feature]
        contrib = contributions[0][i][pos_idx]
        total_contrib += contrib
        print(f"  {feature} ({val}): {contrib:+.4f}")
        
    print(f"\nVerification: Bias ({base_bias:.4f}) + Sum of Contributions ({total_contrib:.4f}) = {base_bias + total_contrib:.4f}")
    
    if abs((base_bias + total_contrib) - pred_prob) < 1e-4:
        print("Success: Bias + Contributions perfectly matches the Predicted Probability!")
    else:
        print("Warning: Bias + Contributions does NOT match the Predicted Probability.")

    # 7. Save Model
    joblib.dump(model, MODEL_PATH)
    print(f"\nModel successfully saved to: {MODEL_PATH}")


if __name__ == "__main__":
    main()
