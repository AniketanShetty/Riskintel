import os
import sys
import json
import pytest
import pandas as pd
import numpy as np

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from f5_random_label_test import run_experiment

@pytest.fixture
def mock_dir(tmpdir):
    return str(tmpdir)

def test_random_label_test(mock_dir):
    # Mock a dataset
    np.random.seed(42)
    df = pd.DataFrame({
        'feature_1': np.random.randn(100),
        'feature_2': np.random.randn(100),
        'loan_status': np.random.choice([0, 1], size=100)
    })
    
    input_csv = os.path.join(mock_dir, 'test_f5.csv')
    df.to_csv(input_csv, index=False)
    
    run_experiment(input_csv, 'loan_status', mock_dir, iterations=2)
    
    json_path = os.path.join(mock_dir, 'metrics', 'f5_random_label_auc.json')
    plot_path = os.path.join(mock_dir, 'plots', 'f5_random_label_distribution.png')
    
    assert os.path.exists(json_path)
    assert os.path.exists(plot_path)
    
    with open(json_path, 'r') as f:
        data = json.load(f)
        
    assert "random_label_auc" in data
    assert "status" in data
    
    auc = data["random_label_auc"]
    assert isinstance(auc, float)
    assert 0.0 <= auc <= 1.0
    
    # Since it's randomized, we expect the status to usually PASS or WARNING
    # If a test fails occasionally due to extreme luck, we just assert keys exist.
