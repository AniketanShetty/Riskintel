import os
import json
import pickle
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'raw', 'External_Cibil_Dataset.csv')
MODEL_DIR = os.path.join(BASE_DIR, 'models', 'archetype')
DEFINITIONS_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'borrower_archetype_definitions.json')

# Features
FEATURES = ['NETMONTHLYINCOME', 'AGE', 'Time_With_Curr_Empr', 'EDUCATION']

# Explicit Ordinal Mapping
EDUCATION_MAP = {
    'OTHERS': 0,
    'SSC': 1,
    '10TH': 1,
    '12TH': 2,
    'UNDER GRADUATE': 3,
    'GRADUATE': 4,
    'POST-GRADUATE': 5,
    'PROFESSIONAL': 6
}

def map_education(val):
    if pd.isna(val):
        return 0
    val_str = str(val).strip().upper()
    return EDUCATION_MAP.get(val_str, 0)

def main():
    print("Loading data...")
    df = pd.read_csv(DATA_PATH)
    
    # Subset and drop NA
    df_arch = df[FEATURES].copy()
    df_arch = df_arch.dropna()
    print(f"Data shape after dropping NA: {df_arch.shape}")
    
    # Apply mapping
    print("Applying ordinal mapping to EDUCATION...")
    df_arch['EDUCATION'] = df_arch['EDUCATION'].apply(map_education)
    
    # Scale
    print("Scaling features...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df_arch)
    
    # Cluster
    print("Fitting KMeans (K=4)...")
    kmeans = KMeans(n_clusters=4, random_state=42)
    kmeans.fit(X_scaled)
    
    # Analyze centroids to label clusters
    centroids_unscaled = scaler.inverse_transform(kmeans.cluster_centers_)
    df_centroids = pd.DataFrame(centroids_unscaled, columns=FEATURES)
    print("\nUnscaled Centroids:")
    print(df_centroids)
    
    # Labeling Logic based on feasibility review insights
    labels_map = {}
    
    # Find the cluster with highest education index
    educated_prof_idx = df_centroids['EDUCATION'].idxmax()
    
    # Find the cluster with highest tenure among the remaining
    remaining_idx = [i for i in range(4) if i != educated_prof_idx]
    tenured_vet_idx = max(remaining_idx, key=lambda i: df_centroids.loc[i, 'Time_With_Curr_Empr'])
    
    # Among the last two, the one with lowest age is Young Starters, other is Mid-Career
    remaining_two = [i for i in remaining_idx if i != tenured_vet_idx]
    young_idx = min(remaining_two, key=lambda i: df_centroids.loc[i, 'AGE'])
    mid_career_idx = [i for i in remaining_two if i != young_idx][0]
    
    labels_map[int(educated_prof_idx)] = "Educated Professionals"
    labels_map[int(tenured_vet_idx)] = "Highly Tenured Veterans"
    labels_map[int(young_idx)] = "Young Starters"
    labels_map[int(mid_career_idx)] = "Mid-Career Established"
    
    print("\nAssigned Labels:")
    for cluster_id, label in labels_map.items():
        print(f"Cluster {cluster_id}: {label}")
        
    # Save artifacts
    print("\nSaving artifacts...")
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    with open(os.path.join(MODEL_DIR, 'scaler.pkl'), 'wb') as f:
        pickle.dump(scaler, f)
        
    with open(os.path.join(MODEL_DIR, 'kmeans_model.pkl'), 'wb') as f:
        pickle.dump(kmeans, f)
        
    os.makedirs(os.path.dirname(DEFINITIONS_PATH), exist_ok=True)
    with open(DEFINITIONS_PATH, 'w') as f:
        json.dump(labels_map, f, indent=4)
        
    print("Training complete and artifacts saved successfully.")

if __name__ == '__main__':
    main()
