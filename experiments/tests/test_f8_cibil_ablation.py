import os
import json
import pytest
import pandas as pd
from unittest.mock import patch, mock_open

# We can import functions from the script directly
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))
from f8_cibil_ablation import train_and_evaluate, generate_report, run_experiment

@pytest.fixture
def mock_dataset(tmp_path):
    # Create a simple dataset with cibil_score and other features
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

def test_train_and_evaluate_ablation():
    # Generate some mock data splits
    data = {
        'cibil_score': [750, 600, 800, 550],
        'income': [50000, 30000, 80000, 20000]
    }
    X_train = pd.DataFrame(data)
    X_test = pd.DataFrame(data)
    y_train = pd.Series([1, 0, 1, 0])
    y_test = pd.Series([1, 0, 1, 0])
    
    # Baseline
    res_base = train_and_evaluate(X_train, X_test, y_train, y_test, is_ablated=False)
    assert res_base['model'] == 'Baseline'
    assert 'auc' in res_base
    assert 'precision' in res_base
    assert 'recall' in res_base
    assert 'f1' in res_base
    
    # Ablated
    X_train_ablated = X_train.drop(columns=['cibil_score'])
    X_test_ablated = X_test.drop(columns=['cibil_score'])
    res_ablated = train_and_evaluate(X_train_ablated, X_test_ablated, y_train, y_test, is_ablated=True)
    assert res_ablated['model'] == 'Ablated'
    assert 'auc' in res_ablated

def test_generate_report(tmp_path):
    base_dir = str(tmp_path)
    os.makedirs(os.path.join(base_dir, 'reports'))
    
    baseline_metrics = {'auc': 0.9988, 'precision': 0.98, 'recall': 0.99, 'f1': 0.985}
    ablated_metrics = {'auc': 0.6500, 'precision': 0.60, 'recall': 0.62, 'f1': 0.61}
    
    generate_report(base_dir, baseline_metrics, ablated_metrics, "FAIL")
    
    report_file = os.path.join(base_dir, 'reports', 'f8_cibil_ablation_report.md')
    assert os.path.exists(report_file)
    with open(report_file, 'r') as f:
        content = f.read()
    
    assert "Verdict: FAIL" in content
    assert "single-feature dominance" in content
    assert "0.9988" in content

@patch('f8_cibil_ablation.plt')
def test_run_experiment(mock_plt, mock_dataset, tmp_path):
    base_dir = str(tmp_path)
    # The setup_dirs in run_experiment will create the directories
    run_experiment(mock_dataset, target_col="loan_status", base_dir=base_dir)
    
    # Verify JSON metrics file
    json_path = os.path.join(base_dir, 'metrics', 'f8_cibil_ablation.json')
    assert os.path.exists(json_path)
    with open(json_path, 'r') as f:
        metrics = json.load(f)
        
    assert 'baseline' in metrics
    assert 'ablated' in metrics
    assert 'status' in metrics
    
    # Check that status logic works on dummy data (it will likely be FAIL for simple dataset or PASS based on seed)
    assert metrics['status'] in ["PASS", "WARNING", "FAIL"]
    
    # Verify plot was created (mocked)
    mock_plt.savefig.assert_called_once()
    
    # Verify report was created
    report_file = os.path.join(base_dir, 'reports', 'f8_cibil_ablation_report.md')
    assert os.path.exists(report_file)
