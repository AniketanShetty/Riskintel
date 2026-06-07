"""Forensic audit of Person A eligibility dataset + model.
Read-only. Trains fresh models on the data and compares.
"""
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import joblib, hashlib
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, roc_auc_score)
from sklearn.inspection import permutation_importance
import shap, json

# 1. Provenance
df = pd.read_csv(r"C:\Users\anike\Desktop\Riskintel\data\processed\eligibility_data.csv")
print("=== 1. PROVENANCE ===")
print(f"shape: {df.shape}")
print(f"columns: {list(df.columns)}")
print(f"sha256[:16]: {hashlib.sha256(df.to_csv(index=False).encode()).hexdigest()[:16]}")
print(f"loan_status balance: {df['loan_status'].value_counts().to_dict()}")
print(f"cibil range: [{df['cibil_score'].min()}, {df['cibil_score'].max()}]")
print(f"any negative loan_amount? {(df['loan_amount']<0).any()}")
print(f"any negative annual_income? {(df['annual_income']<0).any()}")
print(f"any duplicate rows? {df.duplicated().sum()}")
print(f"constant columns: {[c for c in df.columns if df[c].nunique()==1]}")
print()

FEATURES_ALL = ["dependents","education","self_employed","annual_income","loan_amount",
                "loan_term","cibil_score","residential_assets_value",
                "commercial_assets_value","luxury_assets_value","bank_asset_value"]
FEATURES_NO_CIBIL = [f for f in FEATURES_ALL if f != "cibil_score"]

X_all = df[FEATURES_ALL]
X_no_cibil = df[FEATURES_NO_CIBIL]
X_cibil = df[["cibil_score"]]
y = df["loan_status"]

X_train_all, X_test_all, y_train, y_test = train_test_split(
    X_all, y, test_size=0.2, random_state=42, stratify=y)
X_train_noc, X_test_noc = X_train_all[FEATURES_NO_CIBIL], X_test_all[FEATURES_NO_CIBIL]
X_train_ci, X_test_ci = X_train_all[["cibil_score"]], X_test_all[["cibil_score"]]

def fit_eval(model, X_tr, X_te, name):
    model.fit(X_tr, y_train)
    pred = model.predict(X_te)
    prob = model.predict_proba(X_te)[:,1]
    return {
        "name": name,
        "acc": accuracy_score(y_test, pred),
        "prec": precision_score(y_test, pred, zero_division=0),
        "rec": recall_score(y_test, pred, zero_division=0),
        "f1": f1_score(y_test, pred, zero_division=0),
        "auc": roc_auc_score(y_test, prob),
    }, model

print("=== 2+3. MODEL COMPARISON ===")
results = []
configs = [
    (LogisticRegression(max_iter=1000, random_state=42), X_train_ci, X_test_ci, "LR (CIBIL only)"),
    (DecisionTreeClassifier(max_depth=1, random_state=42), X_train_ci, X_test_ci, "DT d=1 (CIBIL only)"),
    (DecisionTreeClassifier(max_depth=2, random_state=42), X_train_ci, X_test_ci, "DT d=2 (CIBIL only)"),
    (DecisionTreeClassifier(max_depth=4, random_state=42), X_train_ci, X_test_ci, "DT d=4 (CIBIL only)"),
    (RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42), X_train_noc, X_test_noc, "RF (excl. CIBIL)"),
    (RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42), X_train_all, X_test_all, "RF (all features)"),
]
models = []
for clf, Xtr, Xte, name in configs:
    m, fitted = fit_eval(clf, Xtr, Xte, name)
    results.append(m)
    models.append(fitted)
    print(f"  {name:35s}  acc={m['acc']:.4f}  prec={m['prec']:.4f}  rec={m['rec']:.4f}  f1={m['f1']:.4f}  auc={m['auc']:.4f}")

# Deployed model
deployed = joblib.load(r"C:\Users\anike\Desktop\Riskintel\models\eligibility\random_forest.joblib")
prob = deployed.predict_proba(X_test_all)[:,1]
pred = (prob >= 0.5).astype(int)
m = {
    "name": "DEPLOYED RF (production model)",
    "acc": accuracy_score(y_test, pred),
    "prec": precision_score(y_test, pred, zero_division=0),
    "rec": recall_score(y_test, pred, zero_division=0),
    "f1": f1_score(y_test, pred, zero_division=0),
    "auc": roc_auc_score(y_test, prob),
}
results.append(m)
print(f"  {m['name']:35s}  acc={m['acc']:.4f}  prec={m['prec']:.4f}  rec={m['rec']:.4f}  f1={m['f1']:.4f}  auc={m['auc']:.4f}")
print()

# 4. SHAP
print("=== 4. SHAP (TreeExplainer, RF all features) ===")
rf_all = models[-1]
explainer = shap.TreeExplainer(rf_all)
sv = explainer.shap_values(X_test_all)
if isinstance(sv, list):
    sv_pos = np.array(sv[1])
elif isinstance(sv, np.ndarray) and sv.ndim == 3:
    sv_pos = sv[:,:,1]
else:
    sv_pos = sv
mean_abs = np.abs(sv_pos).mean(axis=0)
total = mean_abs.sum()
shap_rank = sorted(zip(FEATURES_ALL, mean_abs), key=lambda x: -x[1])
for feat, val in shap_rank:
    print(f"  {feat:30s} {val:.6f}  ({100*val/total:5.2f}%)")
print()

# Permutation importance
print("=== Permutation importance (RF all features) ===")
perm = permutation_importance(rf_all, X_test_all, y_test, n_repeats=10, random_state=42, scoring="roc_auc")
total_p = perm.importances_mean.sum()
perm_rank = sorted(zip(FEATURES_ALL, perm.importances_mean), key=lambda x: -x[1])
for feat, val in perm_rank:
    print(f"  {feat:30s} {val:.6f}  ({100*val/total_p:5.2f}%)")
print()

# 5. Quantify CIBIL contribution
print("=== 5. CIBIL CONTRIBUTION QUANTIFICATION ===")
auc_lr_c = next(r["auc"] for r in results if r["name"]=="LR (CIBIL only)")
auc_rf_noc = next(r["auc"] for r in results if r["name"]=="RF (excl. CIBIL)")
auc_rf_all = next(r["auc"] for r in results if r["name"]=="RF (all features)")
auc_d1 = next(r["auc"] for r in results if r["name"]=="DT d=1 (CIBIL only)")
auc_d2 = next(r["auc"] for r in results if r["name"]=="DT d=2 (CIBIL only)")
auc_d4 = next(r["auc"] for r in results if r["name"]=="DT d=4 (CIBIL only)")

print(f"LR(CIBIL only) AUC:             {auc_lr_c:.4f}")
print(f"DT d=1 (CIBIL only) AUC:        {auc_d1:.4f}")
print(f"DT d=2 (CIBIL only) AUC:        {auc_d2:.4f}")
print(f"DT d=4 (CIBIL only) AUC:        {auc_d4:.4f}")
print(f"RF (no CIBIL) AUC:              {auc_rf_noc:.4f}")
print(f"RF (all features) AUC:          {auc_rf_all:.4f}")
print()
print(f"RF(all) - RF(no CIBIL):           {auc_rf_all - auc_rf_noc:.4f}  (the AUC gain from including CIBIL)")
print(f"LR(CIBIL) - RF(no CIBIL):         {auc_lr_c - auc_rf_noc:.4f}  (the AUC CIBIL alone delivers)")
print(f"% of total gain delivered by CIBIL alone: {100*(auc_lr_c - auc_rf_noc) / max(auc_rf_all - auc_rf_noc, 1e-9):.1f}%")
print()

# 6. DT rules at d=2 and d=4
print("=== 6. DECISION TREE RULES (depth=2, CIBIL only) ===")
dt2 = models[2]
print(export_text(dt2, feature_names=["cibil_score"]))
print()
print("=== DECISION TREE RULES (depth=4, CIBIL only) ===")
dt4 = models[3]
print(export_text(dt4, feature_names=["cibil_score"]))
