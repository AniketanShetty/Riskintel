import os
import json
import pytest
import pandas as pd
from unittest.mock import patch
import numpy as np

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))
from f9_shap_forensics import run_experiment, generate_report, detect_threshold_behavior

@pytest.fixture
def mock_dataset(tmp_path):
    data = {
        'cibil_score': np.random.randint(300, 900, 100),
        'income': np.random.randint(10000, 100000, 100),
        'age': np.random.randint(20, 60, 100)
    }
    # Create deterministic target to force threshold behavior
    data['loan_status'] = [1 if c > 650 else 0 for c in data['cibil_score']]
    
    df = pd.DataFrame(data)
    filepath = tmp_path / "mock_data.csv"
    df.to_csv(filepath, index=False)
    return str(filepath)

def test_detect_threshold_behavior():
    # Pure threshold
    x = np.arange(300, 900)
    y = np.where(x > 650, 0.4, -0.4)
    res = detect_threshold_behavior(y, x)
    assert res == "LIKELY_SYNTHETIC_RULE"
    
    # Random variance (interaction)
    y_interact = y + np.random.normal(0, 0.2, len(x))
    res2 = detect_threshold_behavior(y_interact, x)
    assert res2 == "ORGANIC_INTERACTION"

def test_generate_report(tmp_path):
    base_dir = str(tmp_path)
    os.makedirs(os.path.join(base_dir, 'reports'))
    
    metrics_df = pd.DataFrame({
        'feature': ['cibil_score', 'income', 'age'],
        'mean_abs_shap': [0.4, 0.05, 0.01],
        'pct_total_shap': [86.95, 10.87, 2.17]
    })
    
    generate_report(base_dir, metrics_df, "cibil_score", 86.95, "FAIL", "LIKELY_SYNTHETIC_RULE")
    
    report_file = os.path.join(base_dir, 'reports', 'f9_shap_forensics.md')
    assert os.path.exists(report_file)
    with open(report_file, 'r') as f:
        content = f.read()
    
    assert "LIKELY_SYNTHETIC_RULE" in content
    assert "86.95%" in content
    assert "cibil_score" in content
    assert "reconstructed a hard-coded 'if-else' rule" in content

@patch('f9_shap_forensics.plt')
def test_run_experiment(mock_plt, mock_dataset, tmp_path):
    base_dir = str(tmp_path)
    run_experiment(mock_dataset, target_col="loan_status", base_dir=base_dir)
    
    # Verify CSV file
    csv_path = os.path.join(base_dir, 'metrics', 'f9_shap_summary.csv')
    assert os.path.exists(csv_path)
    df = pd.read_csv(csv_path)
    assert 'feature' in df.columns
    assert 'mean_abs_shap' in df.columns
    assert len(df) == 3 # cibil, income, age
    
    # Verify JSON file
    json_path = os.path.join(base_dir, 'metrics', 'f9_shap_verdict.json')
    assert os.path.exists(json_path)
    with open(json_path, 'r') as f:
        metrics = json.load(f)
        
    assert 'top_feature' in metrics
    assert 'top_feature_pct_contribution' in metrics
    assert 'verdict' in metrics
    assert 'threshold_behavior' in metrics
    assert metrics['verdict'] in ["PASS", "WARNING", "FAIL"]
    
    # Verify plot was created (mocked)
    mock_plt.savefig.assert_called()
    
    # Verify report was created
    report_file = os.path.join(base_dir, 'reports', 'f9_shap_forensics.md')
    assert os.path.exists(report_file)
