import os
import json
import logging
import argparse
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import time
from utils_manifest import generate_manifest

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_dirs(base_dir):
    os.makedirs(os.path.join(base_dir, 'metrics'), exist_ok=True)
    os.makedirs(os.path.join(base_dir, 'plots'), exist_ok=True)

def detect_duplicates(input_path, base_dir):
    start_time = time.time()
    setup_dirs(base_dir)
    logger.info(f"Loading data from {input_path}")
    
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        return

    # Drop explicit ID columns if present (common practice)
    id_cols = [col for col in df.columns if 'id' in col.lower()]
    if id_cols:
        logger.info(f"Dropping ID columns before duplicate check: {id_cols}")
        df = df.drop(columns=id_cols)

    logger.info("Scanning for exact duplicates...")
    is_duplicate = df.duplicated(keep=False)
    duplicate_rows = df[is_duplicate]
    
    total_rows = len(df)
    unique_rows = total_rows - duplicate_rows.shape[0]
    duplicate_row_count = duplicate_rows.shape[0]
    duplicate_percentage = (duplicate_row_count / total_rows) * 100 if total_rows > 0 else 0

    # Save JSON
    stats = {
        'total_rows': total_rows,
        'unique_rows': unique_rows,
        'duplicate_row_count': duplicate_row_count,
        'duplicate_percentage': duplicate_percentage
    }
    json_out = os.path.join(base_dir, 'metrics', 'f3_duplicate_stats.json')
    with open(json_out, 'w') as f:
        json.dump(stats, f, indent=4)
    logger.info(f"Saved JSON to {json_out}")

    # Save CSV
    if duplicate_row_count > 0:
        csv_out = os.path.join(base_dir, 'metrics', 'f3_duplicate_rows.csv')
        duplicate_rows.to_csv(csv_out, index=False)
        logger.info(f"Saved CSV to {csv_out}")

    # Save PNG
    plt.figure(figsize=(8, 6))
    sns.barplot(x=['Unique Rows', 'Duplicate Rows'], y=[unique_rows, duplicate_row_count])
    plt.title("Exact Dataset Duplication")
    plt.ylabel("Count")
    png_out = os.path.join(base_dir, 'plots', 'f3_duplicate_bars.png')
    plt.savefig(png_out)
    plt.close()
    logger.info(f"Saved Plot to {png_out}")

    # Generate Manifest
    execution_duration = time.time() - start_time
    generate_manifest(
        dataset_path=input_path,
        script_name="f3_duplicates",
        execution_duration_seconds=execution_duration,
        output_dir=os.path.join(base_dir, 'metrics')
    )
    logger.info("Saved Run Manifest.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Duplicate Row Detection")
    parser.add_argument("--input", required=True, help="Path to input CSV")
    parser.add_argument("--outdir", default="experiments", help="Base output directory")
    args = parser.parse_args()
    
    detect_duplicates(args.input, args.outdir)
