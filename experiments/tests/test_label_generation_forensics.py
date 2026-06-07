import os
import sys
import tempfile
import pandas as pd
import numpy as np
import pytest

# Add the scripts directory to the path so we can import the script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))

from f7_label_generation_forensics import run_experiment

@pytest.fixture
def mock_data():
    np.random.seed(42)
    # create synthetic data that is completely rule based
    df = pd.DataFrame({
        'cibil_score': np.random.randint(300, 900, 100),
        'annual_income': np.random.randint(100000, 1000000, 100),
        'other_feature': np.random.randn(100)
    })
    # simple rule: if cibil > 700 then 1 else 0
    df['loan_status'] = (df['cibil_score'] > 700).astype(int)
    return df

def test_label_generation_experiment(mock_data):
    with tempfile.TemporaryDirectory() as tmpdir:
        input_csv = os.path.join(tmpdir, 'mock_data.csv')
        mock_data.to_csv(input_csv, index=False)
        
        run_experiment(input_csv, 'loan_status', tmpdir)
        
        # Check files
        assert os.path.exists(os.path.join(tmpdir, 'metrics', 'f7_shallow_tree_metrics.csv'))
        assert os.path.exists(os.path.join(tmpdir, 'reports', 'f7_decision_rules.md'))
        assert os.path.exists(os.path.join(tmpdir, 'metrics', 'f7_feature_usage.csv'))
        assert os.path.exists(os.path.join(tmpdir, 'plots', 'f7_feature_usage.png'))
        assert os.path.exists(os.path.join(tmpdir, 'reports', 'f7_label_generation_verdict.md'))
        
        # Check metrics contents
        metrics = pd.read_csv(os.path.join(tmpdir, 'metrics', 'f7_shallow_tree_metrics.csv'))
        assert len(metrics) == 4
        assert set(metrics['depth'].values) == {1, 2, 3, 4}
        assert 'roc_auc' in metrics.columns
        
        # Due to the simple rule, the tree should achieve 1.0 AUC even at depth 1
        d1_auc = metrics[metrics['depth'] == 1]['roc_auc'].values[0]
        assert d1_auc == 1.0
        
        # Check verdict content
        with open(os.path.join(tmpdir, 'reports', 'f7_label_generation_verdict.md'), 'r') as f:
            content = f.read()
            assert "FAIL" in content or "LIKELY_RULE_GENERATED_DATA" in content

def test_feature_usage_output(mock_data):
    with tempfile.TemporaryDirectory() as tmpdir:
        input_csv = os.path.join(tmpdir, 'mock_data.csv')
        mock_data.to_csv(input_csv, index=False)
        
        run_experiment(input_csv, 'loan_status', tmpdir)
        
        usage = pd.read_csv(os.path.join(tmpdir, 'metrics', 'f7_feature_usage.csv'))
        assert len(usage) > 0
        assert 'feature' in usage.columns
        assert 'usage_count' in usage.columns
        # 'cibil_score' should have been used
        assert 'cibil_score' in usage['feature'].values
