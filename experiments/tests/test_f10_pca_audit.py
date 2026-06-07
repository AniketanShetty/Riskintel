import os
import json
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))
from f10_pca_audit import run_experiment, generate_report, evaluate_overlap

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

def test_evaluate_overlap():
    # Perfectly separated clusters in 2D
    X_pca = np.array([
        [0, 0], [0, 0.1], [0.1, 0],
        [100, 100], [100, 100.1], [100.1, 100]
    ])
    labels = np.array([0, 0, 0, 1, 1, 1])
    
    res = evaluate_overlap(X_pca, labels)
    assert res == "PASS" # High separation
    
    # Perfectly overlapping clusters
    X_pca2 = np.random.randn(100, 2)
    labels2 = np.random.randint(0, 2, 100)
    res2 = evaluate_overlap(X_pca2, labels2)
    assert res2 == "FAIL"

def test_generate_report(tmp_path):
    base_dir = str(tmp_path)
    os.makedirs(os.path.join(base_dir, 'reports'))
    
    pca_metrics = {
        "pc1_variance": 45.0,
        "pc2_variance": 25.0,
        "total_variance_explained": 70.0
    }
    
    generate_report(base_dir, pca_metrics, "FAIL")
    
    report_file = os.path.join(base_dir, 'reports', 'f10_pca_audit.md')
    assert os.path.exists(report_file)
    with open(report_file, 'r') as f:
        content = f.read()
    
    assert "Verdict: FAIL" in content
    assert "70.00%" in content
    assert "single homogeneous cloud" in content

@patch('f10_pca_audit.plt')
def test_run_experiment(mock_plt, mock_dataset, tmp_path):
    base_dir = str(tmp_path)
    run_experiment(mock_dataset, base_dir=base_dir)
    
    # Verify JSON file
    json_path = os.path.join(base_dir, 'metrics', 'f10_pca_variance.json')
    assert os.path.exists(json_path)
    with open(json_path, 'r') as f:
        metrics = json.load(f)
        
    assert 'pc1_variance' in metrics
    assert 'pc2_variance' in metrics
    assert 'total_variance_explained' in metrics
    assert 'verdict' in metrics
    assert metrics['verdict'] in ["PASS", "WARNING", "FAIL"]
    
    # Verify plot was created (mocked)
    mock_plt.savefig.assert_called_once()
    
    # Verify report was created
    report_file = os.path.join(base_dir, 'reports', 'f10_pca_audit.md')
    assert os.path.exists(report_file)
