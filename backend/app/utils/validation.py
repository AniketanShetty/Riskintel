import logging
import pandas as pd


def setup_logger(name: str) -> logging.Logger:
    """Configures and returns a standard logger for preprocessing scripts."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


def validate_shape(df: pd.DataFrame, expected_rows: int, expected_cols: int, dataset_name: str) -> None:
    """Validates that a DataFrame has the exact expected dimensions."""
    if df.shape != (expected_rows, expected_cols):
        raise ValueError(
            f"{dataset_name} shape mismatch. "
            f"Expected ({expected_rows}, {expected_cols}), got {df.shape}."
        )


def validate_no_missing(df: pd.DataFrame, dataset_name: str) -> None:
    """Validates that a DataFrame contains zero missing values."""
    missing = df.isna().sum().sum()
    if missing > 0:
        missing_cols = df.columns[df.isna().any()].tolist()
        raise ValueError(
            f"{dataset_name} has {missing} missing values in columns: {missing_cols}. "
            f"Expected 0 missing values."
        )


def validate_no_negatives(df: pd.DataFrame, columns: list[str], dataset_name: str) -> None:
    """Validates that specified numeric columns contain no negative values."""
    for col in columns:
        if (df[col] < 0).any():
            count = (df[col] < 0).sum()
            raise ValueError(f"{dataset_name} column '{col}' has {count} negative values. Expected 0.")
