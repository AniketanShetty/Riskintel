import os
import sys
import json
import pytest
import pandas as pd
import numpy as np

# Add scripts directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from f1_target_leakage import calculate_leakage
from f2_contamination import detect_contamination
from f3_duplicates import detect_duplicates
from f0_missingness import analyze_missingness
from utils_hashing import canonical_hash_row

@pytest.fixture
def mock_dir(tmpdir):
    return str(tmpdir)

def test_target_leakage(mock_dir):
    # Create dataset with perfect linear correlation
    df = pd.DataFrame({
        'feature_random': np.random.randn(100),
        'loan_status': np.random.choice([0, 1], size=100)
    })
    # Inject leakage
    df['feature_leaked'] = df['loan_status'] * 0.99
    
    input_csv = os.path.join(mock_dir, 'leakage_test.csv')
    df.to_csv(input_csv, index=False)
    
    calculate_leakage(input_csv, 'loan_status', mock_dir)
    
    json_out = os.path.join(mock_dir, 'metrics', 'f1_leakage_summary.json')
    assert os.path.exists(json_out)
    
    with open(json_out, 'r') as f:
        data = json.load(f)
    
    assert data['max_corr_feature'] == 'feature_leaked'
    assert data['max_corr_value'] > 0.90

def test_contamination(mock_dir):
    # This is a bit tricky since the script uses random_state=42 train_test_split.
    # To reliably test it without mocking train_test_split, we just provide a dataset 
    # consisting ENTIRELY of identical rows. Thus train and test will perfectly overlap.
    df = pd.DataFrame({
        'feature_1': [10] * 100,
        'feature_2': [20] * 100,
        'loan_status': [1] * 50 + [0] * 50
    })
    
    input_csv = os.path.join(mock_dir, 'contamination_test.csv')
    df.to_csv(input_csv, index=False)
    
    detect_contamination(input_csv, 'loan_status', mock_dir)
    
    json_out = os.path.join(mock_dir, 'metrics', 'f2_contamination_extended.json')
    assert os.path.exists(json_out)
    
    with open(json_out, 'r') as f:
        data = json.load(f)
        
    # Since all rows are identical (excluding target), there should be exactly 1 unique hash
    # and 20 contaminated test rows (since test size is 20%).
    assert data['unique_overlap_count'] == 1
    assert data['contaminated_row_count'] == 20
    assert data['contaminated_row_pct'] == 100.0

def test_duplicates(mock_dir):
    # Create a dataset where 2 rows are identical copies of each other
    df = pd.DataFrame({
        'id_col': [1, 2, 3, 4], # Should be dropped by logic
        'feature_1': [10, 20, 20, 40],
        'loan_status': [1, 0, 0, 1]
    })
    
    input_csv = os.path.join(mock_dir, 'duplicates_test.csv')
    df.to_csv(input_csv, index=False)
    
    detect_duplicates(input_csv, mock_dir)
    
    json_out = os.path.join(mock_dir, 'metrics', 'f3_duplicate_stats.json')
    assert os.path.exists(json_out)
    
    with open(json_out, 'r') as f:
        data = json.load(f)
        
    assert data['total_rows'] == 4
    # Rows index 1 and 2 are identical (excluding ID). Both are marked as duplicates.
    assert data['duplicate_row_count'] == 2
    assert data['duplicate_percentage'] == 50.0

def test_missingness(mock_dir):
    df = pd.DataFrame({
        'clean_col': [1, 2, 3, 4],
        'missing_col': [1, np.nan, np.nan, np.nan],
        'empty_col': [np.nan, np.nan, np.nan, np.nan],
        'constant_col': [5, 5, 5, 5]
    })
    
    input_csv = os.path.join(mock_dir, 'missingness_test.csv')
    df.to_csv(input_csv, index=False)
    
    analyze_missingness(input_csv, mock_dir)
    
    json_out = os.path.join(mock_dir, 'metrics', 'f0_missingness_summary.json')
    assert os.path.exists(json_out)
    
    with open(json_out, 'r') as f:
        data = json.load(f)
        
    assert data['empty_columns'] == 1
    assert data['near_empty_columns'] == 1
    assert data['constant_columns'] == 1

def test_canonical_hashing():
    row1 = pd.Series({'a': 1.000001, 'b': ' Hello ', 'c': np.nan})
    row2 = pd.Series({'a': 1.00000, 'b': 'hello', 'c': None})
    row3 = pd.Series({'b': 'hello', 'a': 1.00000, 'c': None}) # Order changed
    
    # row1 and row2 should hash identically after canonicalization
    hash1 = canonical_hash_row(row1)
    hash2 = canonical_hash_row(row2)
    hash3 = canonical_hash_row(row3)
    
    assert hash1 == hash2
    assert hash2 == hash3
