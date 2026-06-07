import os
import sys
import json
import pytest
import pandas as pd
import numpy as np

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from f4_single_feature_auc import run_experiment

@pytest.fixture
def mock_dir(tmpdir):
    return str(tmpdir)

def test_single_feature_auc(mock_dir):
    # Mock a dataset where CIBIL is highly correlated with target
    np.random.seed(42)
    loan_status = np.random.choice([0, 1], size=100)
    cibil_score = np.where(loan_status == 1, np.random.randint(700, 900, 100), np.random.randint(300, 600, 100))
    
    df = pd.DataFrame({
        'cibil_score': cibil_score,
        'other_feature': np.random.randn(100),
        'loan_status': loan_status
    })
    
    input_csv = os.path.join(mock_dir, 'test_f4_cibil.csv')
    df.to_csv(input_csv, index=False)
    
    run_experiment(input_csv, 'loan_status', mock_dir)
    
    json_path = os.path.join(mock_dir, 'metrics', 'f4_single_feature_auc.json')
    plot_path = os.path.join(mock_dir, 'plots', 'f4_single_feature_roc.png')
    
    assert os.path.exists(json_path)
    assert os.path.exists(plot_path)
    
    with open(json_path, 'r') as f:
        data = json.load(f)
        
    assert "lr_cibil_auc" in data
    assert "rf_cibil_auc" in data
    assert "full_model_auc" in data
    assert "delta_vs_full_model" in data
    assert "status" in data
    
    for key in ["lr_cibil_auc", "rf_cibil_auc", "full_model_auc"]:
        assert 0.0 <= data[key] <= 1.0
        
    # Given the high correlation we injected, it should trigger a FAIL or WARNING
    assert data['status'] in ["WARNING", "FAIL"]
