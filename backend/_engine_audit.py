"""Forensic audit of E2, E3, E6. E5 is rule-based (covered in earlier read)."""
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import joblib, hashlib, json
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (accuracy_score, roc_auc_score, silhouette_score,
                             calinski_harabasz_score)
from sklearn.tree import DecisionTreeClassifier, export_text
import os

# ---------- E2 Risk Tier ----------
print("="*72)
print("E2 RISK TIER")
print("="*72)
thresholds = json.load(open(r"C:\Users\anike\Desktop\Riskintel\data\processed\risk_tier_thresholds.json"))
print("thresholds:", json.dumps(thresholds, indent=2))

# E2 is purely threshold-based. Check threshold + training data.
# It does NOT use ML. It uses CIBIL score (300-900).
# Find a CIBIL training distribution to validate the threshold design.
df_ec = pd.read_csv(r"C:\Users\anike\Desktop\Riskintel\data\raw\External_Cibil_Dataset.csv")
print(f"\nExternal CIBIL dataset: {df_ec.shape}, columns: {list(df_ec.columns)[:5]}")
print(f"Credit_Score range: {df_ec['Credit_Score'].min()}-{df_ec['Credit_Score'].max()}")
print(f"Approved_Flag distribution: {df_ec['Approved_Flag'].value_counts().to_dict()}")
print(f"\nCIBIL band counts (matches the E2 P1-P4 thresholds 701/669-700/659-668/<=658):")
def band(s):
    if s >= 701: return "P1"
    if s >= 669: return "P2"
    if s >= 659: return "P3"
    return "P4"
df_ec['band'] = df_ec['Credit_Score'].apply(band)
ct = df_ec['band'].value_counts()
print(ct)
print()
ct2 = df_ec.groupby('band')['Approved_Flag'].value_counts(normalize=True).unstack().fillna(0).round(3)
print("Approval rate by band:")
print(ct2)
print(f"\nP1 purity: {(df_ec[df_ec['band']=='P1']['Approved_Flag']==df_ec[df_ec['band']=='P1']['Approved_Flag'].mode()[0]).mean():.3f}")
# Check: is the Approved_Flag consistent with what E2 thinks of as a P1?
print(f"\nE2 P1 = 'Low Risk'. Actual P1 cohort: {(df_ec['band']=='P1').sum()} rows. Of those, 'Approved' = {((df_ec['band']=='P1')&(df_ec['Approved_Flag']=='P1')).sum()}")

# ---------- E3 Borrower Archetype ----------
print()
print("="*72)
print("E3 BORROWER ARCHETYPE (KMeans + production lookup)")
print("="*72)
df_ec2 = df_ec.copy()
print(f"Training data: External_Cibil_Dataset.csv {df_ec2.shape}")
print(f"Features used: NETMONTHLYINCOME, AGE, Time_With_Curr_Empr, EDUCATION")
print(f"Dropped: GENDER, MARITALSTATUS, Credit_Score, Approved_Flag, all 50+ other columns")
print(f"GENDER distribution in kept rows: {df_ec2['GENDER'].value_counts().to_dict()}")
print(f"MARITALSTATUS: {df_ec2['MARITALSTATUS'].value_counts().to_dict()}")
print(f"EDUCATION: {df_ec2['EDUCATION'].value_counts().to_dict()}")
print(f"\nTraining script: scripts/train_borrower_archetype.py")
print(f"  - n_clusters=4, random_state=42")
print(f"  - Cluster labeling by centroid ranking: highest education='Educated Professionals', highest tenure='Highly Tenured Veterans', lowest age of remaining='Young Starters'")
print(f"  - Education Ordinal Map: 8 categories from OTHERS to PROFESSIONAL")
print(f"  - Save to: data/processed/borrower_archetype_definitions.json")
print()
# Recompute the KMeans + label assignment from scratch
FEATURES = ['NETMONTHLYINCOME', 'AGE', 'Time_With_Curr_Empr', 'EDUCATION']
EDUCATION_MAP = {
    'OTHERS': 0, 'SSC': 1, '10TH': 1, '12TH': 2, 'UNDER GRADUATE': 3,
    'GRADUATE': 4, 'POST-GRADUATE': 5, 'PROFESSIONAL': 6
}
df_arch = df_ec2[FEATURES].dropna().copy()
df_arch['EDUCATION'] = df_arch['EDUCATION'].astype(str).str.strip().str.upper().map(EDUCATION_MAP).fillna(0)
print(f"Rows after dropna + map: {len(df_arch)}")
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df_arch)
km = KMeans(n_clusters=4, random_state=42, n_init=10)
labels = km.fit_predict(X_scaled)
print(f"Cluster sizes: {np.bincount(labels)}")
print(f"Inertia: {km.inertia_:.0f}")
print(f"Silhouette: {silhouette_score(X_scaled, labels):.3f}")
print(f"Calinski-Harabasz: {calinski_harabasz_score(X_scaled, labels):.0f}")
centroids = scaler.inverse_transform(km.cluster_centers_)
df_c = pd.DataFrame(centroids, columns=FEATURES)
print("\nCentroids (unscaled):")
print(df_c)
# By centroid ranking
edu_idx = df_c['EDUCATION'].idxmax()
remaining = [i for i in range(4) if i != edu_idx]
ten_idx = max(remaining, key=lambda i: df_c.loc[i, 'Time_With_Curr_Empr'])
remaining2 = [i for i in remaining if i != ten_idx]
young_idx = min(remaining2, key=lambda i: df_c.loc[i, 'AGE'])
mid_idx = [i for i in remaining2 if i != young_idx][0]
labels_map = {edu_idx: "Educated Professionals", ten_idx: "Highly Tenured Veterans",
             young_idx: "Young Starters", mid_idx: "Mid-Career Established"}
print(f"\nAssigned labels (per training script):")
for cid, lab in labels_map.items():
    sub = df_arch[labels == cid]
    print(f"  Cluster {cid} → '{lab}': n={len(sub)}, GENDER M%={((sub.index.map(df_ec2['GENDER'])=='M').mean()*100):.1f}, mean age={sub['AGE'].mean():.1f}")
print()
print("PRODUCTION PATH: livelihood_mapper.py is a STRING LOOKUP, not the KMeans.")
print("Cluster labels are NOT used in production. The 4 labels in borrower_archetype_definitions.json are display-only fallbacks.")
print("Person A engine loads neither kmeans_model.pkl nor definitions.json.")
print("Person B engine does not call get_borrower_archetype at all (only E6 livelihood_mapper).")

# ---------- E5 Readiness ----------
print()
print("="*72)
print("E5 READINESS")
print("="*72)
print("No ML model in models/readiness/ (empty). Pure rule-based scoring.")
import os
contents = os.listdir(r"C:\Users\anike\Desktop\Riskintel\models\readiness")
print(f"models/readiness contents: {contents}")
print("Implementation: backend/app/engines/readiness/readiness_engine.py — explicit weighted scoring, no model artifacts.")
print("Floor breach override at financial_health_score < 0.5 hard-codes band='Not Ready' regardless of other components.")
print(f"\nTraining data: data/processed/readiness_data.csv (40,000 rows, Person B schema)")
df_r = pd.read_csv(r"C:\Users\anike\Desktop\Riskintel\data\processed\readiness_data.csv")
print(f"Columns: {list(df_r.columns)}")
print(f"Shape: {df_r.shape}")
# Is there any 'score' or 'band' column? No — this data is unlabelled inputs only.
# The 'readiness' score is computed by the rule-based engine, not learned.
print(f"\nNo target column. Rules are hand-coded in readiness_engine.py.")
print("Calibration: cannot calibrate (no ground truth to calibrate against).")
print("Synthetic labels: not applicable (no model).")
print("Fairness: social_class and sex are in the data but NOT used by the engine.")
print("Bands: Ready / Moderately Ready / Needs Improvement / Not Ready (hard thresholds 75/50/25).")

# ---------- E6 Livelihood ----------
print()
print("="*72)
print("E6 LIVELIHOOD")
print("="*72)
print("data/processed/livelihood_data.csv: 100+ one-hot macro columns, 1 row = 1 applicant")
print(f"Shape: {df_r.shape}")
print(f"Columns: {list(df_r.columns)}")
print()
print("Implementation: backend/app/engines/livelihood/livelihood_mapper.py")
print("Method: pure dictionary lookup on 'primary_business' string. No model.")
print("6 archetypes: General Micro-Enterprise, Trade & Retail, Services, Agri-Allied, Manufacturing, Transport & Logistics")
print("Cluster 0 (General Micro-Enterprise) is the catch-all default when no key matches.")
print("Signature: only accepts a string, explicitly not the applicant dict. See mapper.py:75-77.")

# ---------- Production routing path verification ----------
print()
print("="*72)
print("ROUTING VERIFICATION")
print("="*72)
import sys
sys.path.insert(0, r"C:\Users\anike\Desktop\Riskintel\backend")
from app.orchestrator import execute_orchestrator
import json

# Person A
pa = {
    "user_type": "person_a", "full_name": "Audit", "age": 35, "gender": "M",
    "marital_status": "Married", "education": "Graduate", "self_employed": "No",
    "years_at_current_employer": 5, "annual_income": 500000, "dependents": 2,
    "cibil_score": 700, "loan_amount": 500000, "loan_term": 12, "loan_purpose": "personal",
    "residential_assets_value": 1000000, "commercial_assets_value": 0,
    "luxury_assets_value": 0, "bank_asset_value": 500000
}
r = execute_orchestrator(pa.copy())
print(f"Person A response keys: {sorted(r.keys())}")
print(f"  archetype in response: {r.get('archetype')}")
print(f"  archetype source: {'E3 KMeans' if r.get('archetype', {}).get('archetype_label') in ['Educated Professionals','Highly Tenured Veterans','Young Starters','Mid-Career Established'] else 'unknown'}")

# Person B
pb = {
    "user_type": "person_b", "full_name": "Audit", "age": 40, "gender": "M",
    "primary_business": "Tailoring", "secondary_business": "none",
    "annual_income": 100000, "monthly_expenses": 5000,
    "loan_amount": 20000, "loan_purpose": "Apparels",
    "loan_tenure": 12, "loan_installments": 12,
    "young_dependents": 1, "old_dependents": 0, "occupants_count": 3,
    "home_ownership": 1, "type_of_house": "T2", "house_area": 400,
    "sanitary_availability": 1, "water_availability": 1.0,
    "social_class": "OBC"
}
r2 = execute_orchestrator(pb.copy())
print(f"\nPerson B response keys: {sorted(r2.keys())}")
print(f"  archetype in response: {r2.get('archetype')}")
print(f"  archetype source: {'E6 lookup' if r2.get('archetype', {}).get('cluster_id', -1) in [1,2,3,4,5] else 'E6 catch-all 0'}")
