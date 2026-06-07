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
from scipy.stats import kruskal
import math

from utils_manifest import generate_manifest

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_dirs(base_dir):
    os.makedirs(os.path.join(base_dir, 'metrics'), exist_ok=True)
    os.makedirs(os.path.join(base_dir, 'plots'), exist_ok=True)
    os.makedirs(os.path.join(base_dir, 'reports'), exist_ok=True)

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

def generate_report(base_dir, verdict, kruskal_df):
    report_content = f"""# E3 Archetype Cluster Profiling Audit

## Overview
This report profiles the RiskIntel Borrower Archetypes (E3) to determine if the clusters differ in statistically and financially meaningful ways. We employ Kruskal-Wallis H-tests to assess variance across non-parametric financial distributions and visualize the centroids via Radar charts.

## Kruskal-Wallis Test Results
| Feature | H-Statistic | p-value |
|---------|-------------|---------|
"""
    for index, row in kruskal_df.iterrows():
        report_content += f"| {row['Feature']} | {row['H-Statistic']:.2f} | {row['p-value']:.4e} |\n"

    report_content += f"""
## Statistical Profiling Verdict
**Verdict:** {verdict}

"""
    if verdict == "PASS":
        report_content += """### Findings
The critical financial variables (`NETMONTHLYINCOME` and `Time_With_Curr_Empr`) exhibit extraordinarily low p-values (p < 0.01) in the Kruskal-Wallis test, indicating that the distributions are statistically distinct across clusters. The radar profiles confirm that the centroids exist in substantially different regions of the feature space.

### Interpretation
**Do these clusters provide actionable borrower segmentation?** Yes. The archetypes are built on robust statistical differences in core financial capacity and stability metrics.
**Are they statistically indistinguishable?** No. They are highly distinguishable.

### Production Implications
The clustering algorithm has successfully identified financially meaningful cohorts. The business can confidently deploy targeted risk strategies (e.g., differential pricing, tailored credit limits) based on these archetypes.
"""
    elif verdict == "WARNING":
        report_content += """### Findings
While some variables show statistical significance (p < 0.05), the radar profiles are mostly overlapping. The differences exist mathematically but may lack practical business magnitude.

### Interpretation
**Do these clusters provide actionable borrower segmentation?** Marginally. The statistical separation is present but weak.
**Are they statistically indistinguishable?** Not mathematically indistinguishable, but potentially practically indistinguishable from a business strategy perspective.

### Production Implications
The archetypes are valid but weak. Consider retraining the model with additional behavioral features or adjusting the number of clusters (K) to force wider separation in the financial dimensions.
"""
    else:
        report_content += """### Findings
The Kruskal-Wallis tests returned p-values > 0.05 for major financial variables, meaning we cannot reject the null hypothesis that these samples originate from the same distribution. The radar profiles are virtually identical.

### Interpretation
**Do these clusters provide actionable borrower segmentation?** No. The clusters represent the exact same financial archetype.
**Are they statistically indistinguishable?** Yes. The segmentation is entirely artificial and unsupported by the underlying financial distributions.

### Production Implications
The model is partitioning identical borrowers into different groups arbitrarily. It provides zero business value and introduces dangerous inconsistency. The E3 model must be removed from production.
"""

    report_path = os.path.join(base_dir, 'reports', 'f12_cluster_profiling.md')
    with open(report_path, 'w') as f:
        f.write(report_content)
    logger.info(f"Saved Markdown report to {report_path}")

def make_radar_chart(df_centroids, features, title, save_path):
    num_vars = len(features)
    # Compute angle for each axis
    angles = [n / float(num_vars) * 2 * math.pi for n in range(num_vars)]
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    ax.set_theta_offset(math.pi / 2)
    ax.set_theta_direction(-1)
    
    # Draw axis lines and labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(features, size=12)
    
    # Scale features between 0 and 1 for radar plot visual parity
    df_scaled = df_centroids.copy()
    for col in features:
        min_val = df_scaled[col].min()
        max_val = df_scaled[col].max()
        if max_val > min_val:
            df_scaled[col] = (df_scaled[col] - min_val) / (max_val - min_val)
        else:
            df_scaled[col] = 0.5
            
    for i in range(len(df_scaled)):
        values = df_scaled.loc[i, features].values.tolist()
        values += values[:1]
        ax.plot(angles, values, linewidth=2, linestyle='solid', label=f'Cluster {i}')
        ax.fill(angles, values, alpha=0.1)
        
    plt.title(title, size=15, y=1.1)
    plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
    
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()

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
    
    logger.info("Fitting KMeans (K=4)...")
    kmeans = KMeans(n_clusters=4, random_state=42)
    labels = kmeans.fit_predict(X_scaled)
    df_arch['Cluster'] = labels
    
    # 1. Cluster Profiles (Means and Medians)
    profiles = []
    for c in sorted(df_arch['Cluster'].unique()):
        c_df = df_arch[df_arch['Cluster'] == c]
        profile = {'Cluster': c}
        for f in FEATURES:
            profile[f'{f}_mean'] = c_df[f].mean()
            profile[f'{f}_median'] = c_df[f].median()
        profiles.append(profile)
        
    profiles_df = pd.DataFrame(profiles)
    profiles_path = os.path.join(base_dir, 'metrics', 'f12_cluster_profiles.csv')
    profiles_df.to_csv(profiles_path, index=False)
    logger.info(f"Saved cluster profiles to {profiles_path}")
    
    # 2. Kruskal-Wallis Tests
    kw_results = []
    for f in FEATURES:
        groups = [df_arch[df_arch['Cluster'] == c][f].values for c in df_arch['Cluster'].unique()]
        try:
            h_stat, p_val = kruskal(*groups)
        except ValueError:
            h_stat, p_val = 0.0, 1.0 # If all values are identical
            
        kw_results.append({
            'Feature': f,
            'H-Statistic': h_stat,
            'p-value': p_val
        })
        
    kw_df = pd.DataFrame(kw_results)
    kw_path = os.path.join(base_dir, 'metrics', 'f12_kruskal_results.csv')
    kw_df.to_csv(kw_path, index=False)
    logger.info(f"Saved Kruskal-Wallis results to {kw_path}")
    
    # 3. Verdict Logic
    # Check Income and Tenure p-values
    income_p = kw_df.loc[kw_df['Feature'] == 'NETMONTHLYINCOME', 'p-value'].values[0]
    tenure_p = kw_df.loc[kw_df['Feature'] == 'Time_With_Curr_Empr', 'p-value'].values[0]
    
    if income_p > 0.05 or tenure_p > 0.05:
        verdict = "FAIL"
    elif income_p < 0.01 and tenure_p < 0.01:
        # Check if radar profiles differ visually
        # We can approximate "radar profiles visibly differ" by checking variance of medians across clusters
        income_medians = profiles_df['NETMONTHLYINCOME_median'].values
        tenure_medians = profiles_df['Time_With_Curr_Empr_median'].values
        
        inc_cv = np.std(income_medians) / (np.mean(income_medians) + 1e-9)
        ten_cv = np.std(tenure_medians) / (np.mean(tenure_medians) + 1e-9)
        
        if inc_cv > 0.1 and ten_cv > 0.1:
            verdict = "PASS"
        else:
            verdict = "WARNING"
    else:
        verdict = "WARNING"
        
    # 4. Radar Chart
    medians_only = profiles_df[['Cluster'] + [f'{f}_median' for f in FEATURES]].copy()
    medians_only.columns = ['Cluster'] + FEATURES
    radar_path = os.path.join(base_dir, 'plots', 'f12_radar_profiles.png')
    make_radar_chart(medians_only, FEATURES, f"Archetype Median Profiles\nVerdict: {verdict}", radar_path)
    logger.info(f"Saved Radar chart to {radar_path}")
    
    # 5. Generate Report
    generate_report(base_dir, verdict, kw_df)
    
    # Generate reproducible manifest
    execution_duration = time.time() - start_time
    generate_manifest(input_path, "f12_cluster_profiling", execution_duration, os.path.join(base_dir, 'metrics'))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cluster Profiling Audit")
    parser.add_argument("--input", required=True, default="../../data/raw/External_Cibil_Dataset.csv")
    parser.add_argument("--outdir", default="experiments")
    args = parser.parse_args()
    
    run_experiment(args.input, args.outdir)
