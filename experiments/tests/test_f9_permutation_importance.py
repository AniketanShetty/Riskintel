import os
import json
import pytest
import pandas as pd
from unittest.mock import patch

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))
from f9_permutation_importance import run_experiment, generate_report

@pytest.fixture
def mock_dataset(tmp_path):
    # Create a simple dataset where cibil_score is highly predictive
    # and income is slightly predictive
    data = {
        'cibil_score': [750, 600, 800, 550, 720, 650, 810, 580, 700, 620] * 10,
        'income': [50000, 30000, 80000, 20000, 45000, 35000, 90000, 25000, 40000, 32000] * 10,
        'age': [30, 25, 45, 22, 35, 28, 50, 24, 32, 26] * 10,
        'loan_status': [1, 0, 1, 0, 1, 0, 1, 0, 1, 0] * 10
    }
    df = pd.DataFrame(data)
    filepath = tmp_path / "mock_data.csv"
    df.to_csv(filepath, index=False)
    return str(filepath)

def test_generate_report(tmp_path):
    base_dir = str(tmp_path)
    os.makedirs(os.path.join(base_dir, 'reports'))
    
    # Mock metrics df
    metrics_df = pd.DataFrame({
        'Feature': ['cibil_score', 'income', 'age'],
        'Importance (Mean)': [0.4, 0.05, 0.01],
        'Importance (Std)': [0.01, 0.005, 0.001],
        'Relative Contribution (%)': [86.95, 10.87, 2.17]
    })
    
    generate_report(base_dir, metrics_df, cibil_dominance=86.95, status="FAIL")
    
    report_file = os.path.join(base_dir, 'reports', 'f9_permutation_importance_report.md')
    assert os.path.exists(report_file)
    with open(report_file, 'r') as f:
        content = f.read()
    
    assert "**Verdict:** FAIL" in content
    assert "86.95%" in content
    assert "cibil_score" in content
    assert "single-feature dominance" in content

@patch('f9_permutation_importance.plt')
def test_run_experiment(mock_plt, mock_dataset, tmp_path):
    base_dir = str(tmp_path)
    # The setup_dirs in run_experiment will create the directories
    run_experiment(mock_dataset, target_col="loan_status", base_dir=base_dir)
    
    # Verify CSV file
    csv_path = os.path.join(base_dir, 'metrics', 'f9_permutation_importance.csv')
    assert os.path.exists(csv_path)
    df = pd.read_csv(csv_path)
    assert 'Feature' in df.columns
    assert 'Importance (Mean)' in df.columns
    assert len(df) == 3 # cibil, income, age
    
    # Verify JSON file
    json_path = os.path.join(base_dir, 'metrics', 'f9_permutation_importance.json')
    assert os.path.exists(json_path)
    with open(json_path, 'r') as f:
        metrics = json.load(f)
        
    assert 'baseline_auc' in metrics
    assert 'total_importance' in metrics
    assert 'cibil_dominance_percentage' in metrics
    assert 'status' in metrics
    assert 'features' in metrics
    assert metrics['status'] in ["PASS", "WARNING", "FAIL"]
    
    # Verify plot was created (mocked)
    mock_plt.savefig.assert_called_once()
    
    # Verify report was created
    report_file = os.path.join(base_dir, 'reports', 'f9_permutation_importance_report.md')
    assert os.path.exists(report_file)
