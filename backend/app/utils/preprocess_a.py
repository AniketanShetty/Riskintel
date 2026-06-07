import os
import pandas as pd
from validation import setup_logger, validate_no_missing, validate_no_negatives

logger = setup_logger("preprocess_a")

def process_dataset_a(input_path: str, output_path: str) -> None:
    logger.info(f"Loading Dataset A from {input_path}...")
    df = pd.read_csv(input_path)
    logger.info(f"Initial shape: {df.shape}")

    # 1. Strip leading spaces from all column names
    df.columns = df.columns.str.strip()

    # 2. Strip leading spaces from specific string columns
    str_cols = ["education", "self_employed", "loan_status"]
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].str.strip()

    # 3. Handle negative values in asset columns
    asset_cols = [
        "residential_assets_value",
        "commercial_assets_value",
        "luxury_assets_value",
        "bank_asset_value"
    ]
    for col in asset_cols:
        if col in df.columns:
            neg_count = (df[col] < 0).sum()
            if neg_count > 0:
                logger.info(f"Clipping {neg_count} negative values in {col} to 0.")
                df[col] = df[col].clip(lower=0)

    # 4. Rename columns to match internal spec
    rename_map = {
        "no_of_dependents": "dependents",
        "income_annum": "annual_income"
    }
    df = df.rename(columns=rename_map)

    # 5. Drop loan_id
    if "loan_id" in df.columns:
        df = df.drop(columns=["loan_id"])

    # 6. Check required columns and apply Encoding
    if "education" in df.columns:
        edu_map = {"Not Graduate": 0, "Graduate": 1}
        unknowns = df[~df["education"].isin(edu_map.keys())]["education"].unique()
        if len(unknowns) > 0:
            raise ValueError(f"Unknown values in education column: {unknowns}")
        df["education"] = df["education"].map(edu_map)
        
    if "self_employed" in df.columns:
        emp_map = {"No": 0, "Yes": 1}
        unknowns = df[~df["self_employed"].isin(emp_map.keys())]["self_employed"].unique()
        if len(unknowns) > 0:
            raise ValueError(f"Unknown values in self_employed column: {unknowns}")
        df["self_employed"] = df["self_employed"].map(emp_map)
        
    if "loan_status" in df.columns:
        status_map = {"Rejected": 0, "Approved": 1}
        unknowns = df[~df["loan_status"].isin(status_map.keys())]["loan_status"].unique()
        if len(unknowns) > 0:
            raise ValueError(f"Unknown values in loan_status column: {unknowns}")
        df["loan_status"] = df["loan_status"].map(status_map)

    # 7. Validation
    logger.info("Running required-column validation...")
    required_cols = [
        "dependents", "education", "self_employed", "annual_income", 
        "loan_amount", "loan_term", "cibil_score", 
        "residential_assets_value", "commercial_assets_value", 
        "luxury_assets_value", "bank_asset_value", "loan_status"
    ]
    
    missing_req_cols = [col for col in required_cols if col not in df.columns]
    if missing_req_cols:
        raise ValueError(f"Eligibility Data is missing required columns: {missing_req_cols}")

    validate_no_missing(df, dataset_name="Eligibility Data")
    
    renamed_asset_cols = [
        "residential_assets_value", 
        "commercial_assets_value", 
        "luxury_assets_value", 
        "bank_asset_value"
    ]
    validate_no_negatives(df, renamed_asset_cols, dataset_name="Eligibility Data")
    
    # 8. Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Successfully saved {output_path}. Final shape: {df.shape}")

if __name__ == "__main__":
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    INPUT_FILE = os.path.join(PROJECT_ROOT, "data", "raw", "loan_approval_dataset.csv")
    OUTPUT_FILE = os.path.join(PROJECT_ROOT, "data", "processed", "eligibility_data.csv")
    process_dataset_a(INPUT_FILE, OUTPUT_FILE)
