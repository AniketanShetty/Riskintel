import os
import json
import logging
import argparse
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import seaborn as sns

from utils_manifest import generate_manifest

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_dirs(base_dir):
    os.makedirs(os.path.join(base_dir, 'metrics'), exist_ok=True)
    os.makedirs(os.path.join(base_dir, 'plots'), exist_ok=True)
    os.makedirs(os.path.join(base_dir, 'reports'), exist_ok=True)

# Identical preprocessing from E3
FEATURES = ['NETMONTHLYINCOME', 'AGE', 'Time_With_Curr_Empr', 'EDUCATION']

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

def generate_report(base_dir, pca_variance, verdict):
    report_content = f"""# E3 Archetype PCA Geometric Validation Report

## Overview
This report applies Principal Component Analysis (PCA) to validate the geometric reality of the E3 Borrower Archetypes (K-Means clusters). The objective is to determine if the clusters represent genuine structural separation in the data or arbitrary algorithmic segmentation.

## PCA Variance Metrics
*   **PC1 Explained Variance:** {pca_variance['pc1_variance']:.2f}%
*   **PC2 Explained Variance:** {pca_variance['pc2_variance']:.2f}%
*   **Total Explained Variance (2D):** {pca_variance['total_variance_explained']:.2f}%

## Geometric Evaluation Verdict
**Verdict:** {verdict}

"""
    if verdict == "PASS":
        report_content += """### Findings
The PCA projection reveals distinct, dense regions corresponding to the cluster assignments. While some boundary overlap exists (typical in real-world data), the cluster cores are mathematically separated in the principal component space.

### Interpretation
**Do natural archetypes appear to exist in the data geometry?** Yes. The clustering algorithm is capturing genuine, distinct multivariate profiles rather than simply drawing arbitrary lines through a homogeneous cloud.
**Would a human visually identify these clusters without being told K=4?** Yes, distinct lobes or dense focal points are visually apparent in the 2D projection.

### Production Implications
The E3 Archetype Engine provides legitimate business value by identifying true sub-populations of borrowers. Keep the model in production.
"""
    elif verdict == "WARNING":
        report_content += """### Findings
The clusters overlap significantly, though visual inspection reveals maintaining core densities. The principal components capture moderate variance, but the cluster boundaries in 2D space are highly ambiguous.

### Interpretation
**Do natural archetypes appear to exist in the data geometry?** Partially. There is a general structural gradient (e.g., from young/low-income to old/high-income), but hard categorical boundaries are forced.
**Would a human visually identify these clusters without being told K=4?** Unlikely. A human would likely see a single continuous mass with varying density, not 4 distinct groups.

### Production Implications
The clusters exist but are statistically weak. The model may require retraining using different feature engineering (e.g., K-Prototypes to better handle categorical data like Education) to achieve better separation.
"""
    else:
        report_content += """### Findings
The PCA projection shows a single homogeneous cloud of data points. The K-Means algorithm has arbitrarily sliced a continuous distribution into 4 pieces. The cluster labels show massive overlap with no discernible geometric separation.

### Interpretation
**Do natural archetypes appear to exist in the data geometry?** No. The data represents a continuous spectrum of borrowers without natural dividing lines or dense sub-populations.
**Would a human visually identify these clusters without being told K=4?** Absolutely not. The assignment of K=4 forces arbitrary cutoffs on continuous variables.

### Production Implications
The E3 Archetype model is an illusion of segmentation. It is classifying indistinguishable borrowers into different archetypes based on microscopic coordinate differences near the arbitrary boundaries. The model should be removed from the RiskIntel platform unless a stronger feature space can be engineered.
"""

    report_path = os.path.join(base_dir, 'reports', 'f10_pca_audit.md')
    with open(report_path, 'w') as f:
        f.write(report_content)
    logger.info(f"Saved Markdown report to {report_path}")

def evaluate_overlap(X_pca, labels):
    """
    Heuristic to evaluate overlap based on distance between cluster centroids
    vs average cluster spread (silhouette-like concept but simpler for PCA).
    """
    centroids = []
    spreads = []
    
    for i in np.unique(labels):
        cluster_pts = X_pca[labels == i]
        centroid = np.mean(cluster_pts, axis=0)
        # Average distance to centroid for points in this cluster
        spread = np.mean(np.linalg.norm(cluster_pts - centroid, axis=1))
        centroids.append(centroid)
        spreads.append(spread)
        
    centroids = np.array(centroids)
    mean_spread = np.mean(spreads)
    
    # Calculate pairwise distances between centroids
    distances = []
    for i in range(len(centroids)):
        for j in range(i+1, len(centroids)):
            dist = np.linalg.norm(centroids[i] - centroids[j])
            distances.append(dist)
            
    mean_dist = np.mean(distances)
    
    # Ratio of distance between clusters to internal spread
    separation_ratio = mean_dist / mean_spread
    
    if separation_ratio > 1.5:
        return "PASS"
    elif separation_ratio > 0.8:
        return "WARNING"
    else:
        return "FAIL"

def run_experiment(input_path, base_dir):
    start_time = time.time()
    setup_dirs(base_dir)
    logger.info(f"Loading data from {input_path}")
    
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        return
        
    # Preprocessing
    df_arch = df[FEATURES].copy()
    df_arch = df_arch.dropna()
    df_arch['EDUCATION'] = df_arch['EDUCATION'].apply(map_education)
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df_arch)
    
    # Clustering (re-run K=4 to get labels)
    logger.info("Fitting KMeans (K=4)...")
    kmeans = KMeans(n_clusters=4, random_state=42)
    labels = kmeans.fit_predict(X_scaled)
    
    # PCA
    logger.info("Performing PCA (n_components=2)...")
    pca = PCA(n_components=2, random_state=42)
    X_pca = pca.fit_transform(X_scaled)
    
    # Variance metrics
    pc1_var = pca.explained_variance_ratio_[0] * 100
    pc2_var = pca.explained_variance_ratio_[1] * 100
    total_var = pc1_var + pc2_var
    
    pca_metrics = {
        "pc1_variance": float(pc1_var),
        "pc2_variance": float(pc2_var),
        "total_variance_explained": float(total_var)
    }
    
    # Verdict heuristic
    verdict = evaluate_overlap(X_pca, labels)
    
    # Force WARNING if total variance explained is very low despite "separation"
    if verdict == "PASS" and total_var < 40.0:
        verdict = "WARNING"
        
    pca_metrics["verdict"] = verdict

    # Save JSON
    json_path = os.path.join(base_dir, 'metrics', 'f10_pca_variance.json')
    with open(json_path, 'w') as f:
        json.dump(pca_metrics, f, indent=4)
    logger.info(f"Saved PCA variance metrics to {json_path}")
    
    # Plotting
    plt.figure(figsize=(10, 8))
    # We sample to avoid plotting millions of points and obscuring density
    if len(X_pca) > 10000:
        idx = np.random.choice(len(X_pca), 10000, replace=False)
        X_plot = X_pca[idx]
        labels_plot = labels[idx]
    else:
        X_plot = X_pca
        labels_plot = labels
        
    scatter = plt.scatter(X_plot[:, 0], X_plot[:, 1], c=labels_plot, cmap='viridis', alpha=0.5, s=15, edgecolors='none')
    plt.colorbar(scatter, label='Cluster Label')
    plt.xlabel(f'Principal Component 1 ({pc1_var:.1f}% Variance)')
    plt.ylabel(f'Principal Component 2 ({pc2_var:.1f}% Variance)')
    plt.title(f'PCA Projection of Borrower Archetypes (K=4)\nVerdict: {verdict}')
    plt.grid(True, linestyle='--', alpha=0.3)
    
    plot_path = os.path.join(base_dir, 'plots', 'f10_pca_clusters.png')
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved PCA scatter plot to {plot_path}")

    # Generate Report
    generate_report(base_dir, pca_metrics, verdict)
    
    # Generate reproducible manifest
    execution_duration = time.time() - start_time
    generate_manifest(input_path, "f10_pca_audit", execution_duration, os.path.join(base_dir, 'metrics'))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PCA Geometric Validation Audit")
    parser.add_argument("--input", required=True, default="../../data/raw/External_Cibil_Dataset.csv")
    parser.add_argument("--outdir", default="experiments")
    args = parser.parse_args()
    
    run_experiment(args.input, args.outdir)
