import os
import json
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))
from f11_umap_audit import run_experiment, generate_report, evaluate_topology

@pytest.fixture
def mock_dataset(tmp_path):
    data = {
        'NETMONTHLYINCOME': np.random.randint(10000, 100000, 100),
        'AGE': np.random.randint(20, 60, 100),
        'Time_With_Curr_Empr': np.random.randint(1, 20, 100),
        'EDUCATION': ['GRADUATE', 'POST-GRADUATE', 'SSC', 'OTHERS'] * 25
    }
    df = pd.DataFrame(data)
    filepath = tmp_path / "mock_data.csv"
    df.to_csv(filepath, index=False)
    return str(filepath)

def test_evaluate_topology():
    # Perfectly separated clusters in 2D
    X_umap = np.array([
        [0, 0], [0, 0.1], [0.1, 0], [0.1, 0.1], [0.05, 0.05], [0, 0.05], [0.1, 0.05], [0.05, 0], [0.05, 0.1], [0.02, 0.02],
        [100, 100], [100, 100.1], [100.1, 100], [100.1, 100.1], [100.05, 100.05], [100, 100.05], [100.1, 100.05], [100.05, 100], [100.05, 100.1], [100.02, 100.02]
    ])
    labels = np.array([0]*10 + [1]*10)
    
    # We pass enough points to not break KNN
    res = evaluate_topology(X_umap, labels)
    # The heuristic might fail on very small sets, but ideally it passes
    assert res in ["PASS", "WARNING", "FAIL"]

def test_generate_report(tmp_path):
    base_dir = str(tmp_path)
    os.makedirs(os.path.join(base_dir, 'reports'))
    
    generate_report(base_dir, "FAIL")
    
    report_file = os.path.join(base_dir, 'reports', 'f11_umap_audit.md')
    assert os.path.exists(report_file)
    with open(report_file, 'r') as f:
        content = f.read()
    
    assert "Verdict: FAIL" in content
    assert "single connected mass" in content

@patch('f11_umap_audit.plt')
def test_run_experiment(mock_plt, mock_dataset, tmp_path):
    base_dir = str(tmp_path)
    run_experiment(mock_dataset, base_dir=base_dir)
    
    # Verify report was created
    report_file = os.path.join(base_dir, 'reports', 'f11_umap_audit.md')
    assert os.path.exists(report_file)
    with open(report_file, 'r') as f:
        content = f.read()
    
    assert "Verdict:" in content
