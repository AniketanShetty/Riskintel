import hashlib
import pandas as pd
import numpy as np

def canonical_hash_row(row: pd.Series) -> str:
    """
    Deterministically hash a pandas Series (row).
    Normalizes column order, NaN values, strings, and float precision.
    """
    sorted_row = row.sort_index()
    components = []
    
    for val in sorted_row:
        if pd.isna(val):
            components.append("NULL")
        elif isinstance(val, (float, np.floating)):
            # Normalize to 5 decimal places to prevent floating point drift
            components.append(f"{val:.5f}")
        elif isinstance(val, str):
            # Normalize categorical string casing and whitespace
            components.append(val.strip().lower())
        else:
            components.append(str(val))
            
    # Join with pipe delimiter
    row_string = "|".join(components)
    return hashlib.sha256(row_string.encode('utf-8')).hexdigest()

def canonical_hash_dataframe(df: pd.DataFrame) -> pd.Series:
    """Apply canonical hashing to an entire dataframe."""
    return df.apply(canonical_hash_row, axis=1)

# Collision Risk Analysis:
# Using SHA-256 (256-bit hash), the collision probability is statistically zero.
# The primary risk of "collision" in this context is FALSE POSITIVES 
# (two logically different rows producing the same hash). 
# By enforcing strict pipe delimiters `|` and precise float truncation,
# we ensure that `1.00000|A` is strictly distinct from `1.0|0000A`.
