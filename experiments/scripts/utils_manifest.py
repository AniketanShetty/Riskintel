import os
import sys
import json
import time
import hashlib
import platform
import subprocess
from datetime import datetime, timezone

import pandas as pd
import sklearn
import scipy
import matplotlib

def get_file_sha256(filepath):
    """Compute the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception:
        return None

def get_git_commit_hash(base_dir):
    """Attempt to retrieve the current git commit hash."""
    try:
        commit = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], 
            cwd=base_dir, 
            stderr=subprocess.DEVNULL
        )
        return commit.decode('utf-8').strip()
    except Exception:
        return "git_not_found_or_not_repo"

def generate_manifest(dataset_path, script_name, execution_duration_seconds, output_dir):
    """Generate and save the ML Reproducibility Run Manifest."""
    base_git_dir = os.path.dirname(os.path.abspath(dataset_path))
    
    manifest = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_path": os.path.abspath(dataset_path),
        "dataset_sha256": get_file_sha256(dataset_path),
        "git_commit_hash": get_git_commit_hash(base_git_dir),
        "python_version": sys.version.split(' ')[0],
        "operating_system": platform.platform(),
        "pandas_version": pd.__version__,
        "sklearn_version": sklearn.__version__,
        "scipy_version": scipy.__version__,
        "matplotlib_version": matplotlib.__version__,
        "script_name": script_name,
        "execution_duration_seconds": round(execution_duration_seconds, 4)
    }
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Save a manifest specifically for this script run
    manifest_path = os.path.join(output_dir, f"run_manifest_{script_name}.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=4)
        
    return manifest
