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
from sklearn.neighbors import NearestNeighbors

try:
    import umap
except ImportError:
    umap = None

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

def generate_report(base_dir, verdict):
    report_content = f"""# E3 Archetype UMAP Topology Audit Report

## Overview
This report applies Uniform Manifold Approximation and Projection (UMAP) to evaluate the non-linear geometric structure of the E3 Borrower Archetypes (K-Means clusters). The objective is to determine if the discovered clusters represent genuine structural manifolds in the dataset, or if KMeans has simply arbitrarily partitioned a continuous cloud of points.

## Topology Evaluation Verdict
**Verdict:** {verdict}

"""
    if verdict == "PASS":
        report_content += """### Findings
The UMAP projection reveals clearly separated geometric islands corresponding to the cluster assignments. 

### Interpretation
**Does UMAP reveal genuine latent borrower structure?** Yes. The non-linear projection confirms the presence of structurally distinct sub-populations in the underlying financial behavior. The data topology naturally forms distinct groups.
**Has KMeans simply partitioned a continuous cloud?** No. The KMeans algorithm successfully mapped its centroids to genuine structural clusters existing within the non-linear manifold of the data.

### Production Implications
The E3 Archetype Engine captures real, distinct borrower profiles. The segmentation is robust. Keep the model in production.
"""
    elif verdict == "WARNING":
        report_content += """### Findings
The UMAP projection reveals connected clusters with significant bottlenecks, or distinct regions that maintain tenuous structural bridges. 

### Interpretation
**Does UMAP reveal genuine latent borrower structure?** Partially. There is visible non-linear structure with varying densities, but the clusters are not entirely isolated. They exist as distinct lobes within a broader connected manifold.
**Has KMeans simply partitioned a continuous cloud?** It has partitioned a structured, lumpy cloud. The boundaries between clusters may be somewhat arbitrary where the structural bottlenecks occur, but the core regions are meaningful.

### Production Implications
The clusters represent meaningful variations but are not completely disconnected sub-populations. Consider exploring fuzzy clustering or mixture models if hard boundaries are causing business logic issues, but the current segmentation retains value.
"""
    else:
        report_content += """### Findings
The UMAP projection shows a single connected mass. The cluster labels are heavily overlapping within this continuous topological structure.

### Interpretation
**Does UMAP reveal genuine latent borrower structure?** No. The non-linear projection confirms that the data forms a single, continuous manifold without distinct islands or structural bottlenecks.
**Has KMeans simply partitioned a continuous cloud?** Yes. KMeans has artificially sliced a homogeneous continuous distribution into 4 pieces. The boundaries are mathematically arbitrary.

### Production Implications
The model is forcing categorical segmentation onto a continuous spectrum. This provides an illusion of distinct archetypes where none exist topologically. The E3 Archetype model should be removed or completely re-engineered.
"""

    report_path = os.path.join(base_dir, 'reports', 'f11_umap_audit.md')
    with open(report_path, 'w') as f:
        f.write(report_content)
    logger.info(f"Saved Markdown report to {report_path}")

def evaluate_topology(X_umap, labels):
    """
    Heuristic to evaluate overlap and topology in UMAP space.
    Calculates the proportion of k-nearest neighbors that share the same cluster label.
    If the clusters are well separated (islands), neighbors should almost always share the same label.
    """
    if len(X_umap) > 5000:
        idx = np.random.choice(len(X_umap), 5000, replace=False)
        X_eval = X_umap[idx]
        labels_eval = labels[idx]
    else:
        X_eval = X_umap
        labels_eval = labels
        
    nbrs = NearestNeighbors(n_neighbors=15, algorithm='ball_tree').fit(X_eval)
    distances, indices = nbrs.kneighbors(X_eval)
    
    same_label_counts = []
    for i in range(len(X_eval)):
        # indices[i] includes the point itself at position 0 usually
        neighbor_labels = labels_eval[indices[i][1:]] 
        my_label = labels_eval[i]
        same_label_ratio = np.mean(neighbor_labels == my_label)
        same_label_counts.append(same_label_ratio)
        
    mean_homogeneity = np.mean(same_label_counts)
    logger.info(f"Local neighborhood label homogeneity: {mean_homogeneity:.3f}")
    
    if mean_homogeneity > 0.90:
        return "PASS"
    elif mean_homogeneity > 0.70:
        return "WARNING"
    else:
        return "FAIL"

def run_experiment(input_path, base_dir):
    if umap is None:
        logger.error("umap-learn is not installed. Run `pip install umap-learn`")
        return
        
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
    
    # Subsample for UMAP performance if dataset is large
    # UMAP can be slow on >50k rows
    if len(X_scaled) > 15000:
        np.random.seed(42)
        idx = np.random.choice(len(X_scaled), 15000, replace=False)
        X_scaled_sample = X_scaled[idx]
    else:
        X_scaled_sample = X_scaled
    
    # Clustering (re-run K=4 to get labels for the sample)
    logger.info("Fitting KMeans (K=4)...")
    kmeans = KMeans(n_clusters=4, random_state=42)
    labels = kmeans.fit_predict(X_scaled_sample)
    
    # UMAP
    logger.info("Performing UMAP projection...")
    reducer = umap.UMAP(random_state=42, n_neighbors=30, min_dist=0.1)
    X_umap = reducer.fit_transform(X_scaled_sample)
    
    # Verdict heuristic
    verdict = evaluate_topology(X_umap, labels)
    
    # Plotting
    plt.figure(figsize=(10, 8))
    scatter = plt.scatter(X_umap[:, 0], X_umap[:, 1], c=labels, cmap='viridis', alpha=0.6, s=10, edgecolors='none')
    plt.colorbar(scatter, label='Cluster Label')
    plt.xlabel('UMAP Dimension 1')
    plt.ylabel('UMAP Dimension 2')
    plt.title(f'UMAP Topology of Borrower Archetypes (K=4)\nVerdict: {verdict}')
    plt.grid(False)
    
    plot_path = os.path.join(base_dir, 'plots', 'f11_umap_clusters.png')
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved UMAP scatter plot to {plot_path}")

    # Generate Report
    generate_report(base_dir, verdict)
    
    # Generate reproducible manifest
    execution_duration = time.time() - start_time
    generate_manifest(input_path, "f11_umap_audit", execution_duration, os.path.join(base_dir, 'metrics'))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UMAP Topology Validation Audit")
    parser.add_argument("--input", required=True, default="../../data/raw/External_Cibil_Dataset.csv")
    parser.add_argument("--outdir", default="experiments")
    args = parser.parse_args()
    
    run_experiment(args.input, args.outdir)
