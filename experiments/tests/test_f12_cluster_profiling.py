import os
import json
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))
from f12_cluster_profiling import run_experiment, generate_report, make_radar_chart

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

def test_generate_report(tmp_path):
    base_dir = str(tmp_path)
    os.makedirs(os.path.join(base_dir, 'reports'))
    
    kw_df = pd.DataFrame({
        'Feature': ['NETMONTHLYINCOME', 'AGE'],
        'H-Statistic': [50.0, 45.0],
        'p-value': [1e-10, 1e-8]
    })
    
    generate_report(base_dir, "PASS", kw_df)
    
    report_file = os.path.join(base_dir, 'reports', 'f12_cluster_profiling.md')
    assert os.path.exists(report_file)
    with open(report_file, 'r') as f:
        content = f.read()
    
    assert "Verdict: PASS" in content
    assert "1.0000e-10" in content

@patch('f12_cluster_profiling.plt')
def test_run_experiment(mock_plt, mock_dataset, tmp_path):
    base_dir = str(tmp_path)
    run_experiment(mock_dataset, base_dir=base_dir)
    
    # Verify CSV files
    kw_path = os.path.join(base_dir, 'metrics', 'f12_kruskal_results.csv')
    assert os.path.exists(kw_path)
    kw_df = pd.read_csv(kw_path)
    assert 'Feature' in kw_df.columns
    assert 'p-value' in kw_df.columns
    
    profiles_path = os.path.join(base_dir, 'metrics', 'f12_cluster_profiles.csv')
    assert os.path.exists(profiles_path)
    prof_df = pd.read_csv(profiles_path)
    assert 'Cluster' in prof_df.columns
    assert 'NETMONTHLYINCOME_mean' in prof_df.columns
    
    # Verify plot was created (mocked)
    mock_plt.savefig.assert_called()
    
    # Verify report was created
    report_file = os.path.join(base_dir, 'reports', 'f12_cluster_profiling.md')
    assert os.path.exists(report_file)
