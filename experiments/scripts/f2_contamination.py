import os
import json
import logging
import argparse
import hashlib
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib_venn import venn2
from sklearn.model_selection import train_test_split
import time
from utils_manifest import generate_manifest
from utils_hashing import canonical_hash_dataframe

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_dirs(base_dir):
    os.makedirs(os.path.join(base_dir, 'metrics'), exist_ok=True)
    os.makedirs(os.path.join(base_dir, 'plots'), exist_ok=True)

def detect_contamination(input_path, target_col, base_dir):
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

    logger.info("Splitting dataset exactly as in train.py (80/20, random_state=42)")
    X_train, X_test, _, _ = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    logger.info("Hashing rows canonically...")
    train_hashes_series = canonical_hash_dataframe(X_train)
    test_hashes_series = canonical_hash_dataframe(X_test)
    
    train_hashes_unique = set(train_hashes_series)
    test_hashes_unique = set(test_hashes_series)

    logger.info("Calculating unique and row-level intersections...")
    unique_overlap = train_hashes_unique.intersection(test_hashes_unique)
    unique_overlap_count = len(unique_overlap)
    unique_overlap_pct = (unique_overlap_count / len(test_hashes_unique)) * 100 if len(test_hashes_unique) > 0 else 0
    
    contaminated_test_rows = test_hashes_series[test_hashes_series.isin(train_hashes_unique)]
    contaminated_row_count = len(contaminated_test_rows)
    contaminated_row_pct = (contaminated_row_count / len(test_hashes_series)) * 100 if len(test_hashes_series) > 0 else 0

    # Save JSON
    report = {
        'total_train_rows': len(train_hashes_series),
        'total_test_rows': len(test_hashes_series),
        'unique_overlap_count': unique_overlap_count,
        'unique_overlap_pct': round(unique_overlap_pct, 4),
        'contaminated_row_count': contaminated_row_count,
        'contaminated_row_pct': round(contaminated_row_pct, 4),
        'affected_test_rows': contaminated_row_count
    }
    json_out = os.path.join(base_dir, 'metrics', 'f2_contamination_extended.json')
    with open(json_out, 'w') as f:
        json.dump(report, f, indent=4)
    logger.info(f"Saved JSON to {json_out}")

    # Save CSV
    if unique_overlap_count > 0:
        overlap_df = pd.DataFrame({'contaminated_hash': list(unique_overlap)})
        csv_out = os.path.join(base_dir, 'metrics', 'f2_contaminated_hashes.csv')
        overlap_df.to_csv(csv_out, index=False)
        logger.info(f"Saved CSV to {csv_out}")

    # Save PNG
    plt.figure(figsize=(8, 6))
    venn2(subsets=(len(train_hashes_unique - test_hashes_unique), 
                   len(test_hashes_unique - train_hashes_unique), 
                   unique_overlap_count),
          set_labels=('Train Hashes', 'Test Hashes'))
    plt.title("Train/Test Leakage (Row Contamination)")
    png_out = os.path.join(base_dir, 'plots', 'f2_venn_diagram.png')
    plt.savefig(png_out)
    plt.close()
    logger.info(f"Saved Plot to {png_out}")

    # Generate Manifest
    execution_duration = time.time() - start_time
    generate_manifest(
        dataset_path=input_path,
        script_name="f2_contamination",
        execution_duration_seconds=execution_duration,
        output_dir=os.path.join(base_dir, 'metrics')
    )
    logger.info("Saved Run Manifest.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train/Test Contamination Detection")
    parser.add_argument("--input", required=True, help="Path to input CSV")
    parser.add_argument("--target", required=True, help="Target column name")
    parser.add_argument("--outdir", default="experiments", help="Base output directory")
    args = parser.parse_args()
    
    detect_contamination(args.input, args.target, args.outdir)
