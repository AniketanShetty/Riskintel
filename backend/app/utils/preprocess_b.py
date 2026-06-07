import os
import pandas as pd
from validation import setup_logger, validate_no_missing

logger = setup_logger("preprocess_b")

def process_dataset_b(input_path: str, readiness_out: str, livelihood_out: str) -> None:
    logger.info(f"Loading Dataset B from {input_path}...")
    df = pd.read_csv(input_path)
    logger.info(f"Initial shape: {df.shape}")

    # 1. Drop Id column
    if "Id" in df.columns:
        df = df.drop(columns=["Id"])

    # 2. Fix typos
    if "water_availabity" in df.columns:
        df = df.rename(columns={"water_availabity": "water_availability"})

    # 3. Handle Missing Values Dynamically
    monthly_expenses_fill = df["monthly_expenses"].median() if "monthly_expenses" in df.columns else 0
    home_ownership_fill = df["home_ownership"].mode()[0] if "home_ownership" in df.columns and not df["home_ownership"].mode().empty else 1.0
    type_of_house_fill = df["type_of_house"].mode()[0] if "type_of_house" in df.columns and not df["type_of_house"].mode().empty else "Unknown"
    sanitary_fill = df["sanitary_availability"].mode()[0] if "sanitary_availability" in df.columns and not df["sanitary_availability"].mode().empty else 1.0
    water_fill = df["water_availability"].median() if "water_availability" in df.columns else 0.5
    primary_biz_fill = df["primary_business"].mode()[0] if "primary_business" in df.columns and not df["primary_business"].mode().empty else "Unknown"
    purpose_fill = df["loan_purpose"].mode()[0] if "loan_purpose" in df.columns and not df["loan_purpose"].mode().empty else "Unknown"

    fill_rules = {
        "city": "Unknown",
        "social_class": "Unknown",
        "secondary_business": "none",
        "monthly_expenses": monthly_expenses_fill,
        "home_ownership": home_ownership_fill,
        "type_of_house": type_of_house_fill,
        "sanitary_availability": sanitary_fill,
        "water_availability": water_fill,
        "primary_business": primary_biz_fill,
        "loan_purpose": purpose_fill
    }

    for col, fill_val in fill_rules.items():
        if col in df.columns:
            missing_cnt = df[col].isna().sum()
            if missing_cnt > 0:
                logger.info(f"Filling {missing_cnt} missing values in {col} with computed value: {fill_val}")
                df[col] = df[col].fillna(fill_val)

    # Save readiness_data.csv BEFORE one-hot encoding
    logger.info("Running validation for Readiness Data...")
    validate_no_missing(df, dataset_name="Readiness Data")
    
    os.makedirs(os.path.dirname(readiness_out), exist_ok=True)
    df.to_csv(readiness_out, index=False)
    logger.info(f"Saved {readiness_out}. Shape: {df.shape}")

    # 4. Extract Livelihood Features
    livelihood_cols = [
        "primary_business", "annual_income", "monthly_expenses", 
        "loan_amount", "loan_purpose", "home_ownership", "type_of_house"
    ]
    df_liv = df[livelihood_cols].copy()

    # 5. Macro-category mapping
    def map_business(x):
        x = str(x).lower()
        if any(w in x for w in ['farm', 'rear', 'dairy', 'goat', 'cow', 'agri']):
            return 'Agriculture'
        elif any(w in x for w in ['tailor', 'grocer', 'vendor', 'shop', 'retail']):
            return 'Retail'
        elif any(w in x for w in ['loom', 'handicraft', 'manufact', 'produc', 'weaver']):
            return 'Production'
        else:
            return 'Services'

    def map_purpose(x):
        x = str(x).lower()
        if any(w in x for w in ['crop', 'livestock', 'agro', 'anim']):
            return 'Agriculture'
        elif any(w in x for w in ['house', 'construct', 'repair']):
            return 'Housing'
        elif any(w in x for w in ['work', 'capit', 'equip', 'raw', 'business']):
            return 'Business'
        else:
            return 'Personal'

    logger.info("Applying macro-category mappings for Livelihood Data...")
    df_liv["primary_business_macro"] = df_liv["primary_business"].apply(map_business)
    df_liv["loan_purpose_macro"] = df_liv["loan_purpose"].apply(map_purpose)

    # Drop original columns to avoid redundancy
    df_liv = df_liv.drop(columns=["primary_business", "loan_purpose"])

    # 6. One-hot encoding macro-categories and type_of_house natively
    logger.info("Applying one-hot encoding to macro-categories and type_of_house...")
    df_liv = pd.get_dummies(df_liv, columns=["primary_business_macro", "loan_purpose_macro", "type_of_house"], drop_first=False)
    
    # Ensure boolean outputs are converted to int
    for col in df_liv.columns:
        if df_liv[col].dtype == 'bool':
            df_liv[col] = df_liv[col].astype(int)

    # 7. Validation for Livelihood
    logger.info("Running validation for Livelihood Data...")
    if len(df_liv.columns) < 10:
        raise ValueError(f"Livelihood Data has too few columns after one-hot encoding. Expected >= 10, got {len(df_liv.columns)}.")
    
    validate_no_missing(df_liv, dataset_name="Livelihood Data")

    df_liv.to_csv(livelihood_out, index=False)
    logger.info(f"Saved {livelihood_out}. Shape: {df_liv.shape}")

if __name__ == "__main__":
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    INPUT_FILE = os.path.join(PROJECT_ROOT, "data", "raw", "RuralCreditData.csv")
    READINESS_OUT = os.path.join(PROJECT_ROOT, "data", "processed", "readiness_data.csv")
    LIVELIHOOD_OUT = os.path.join(PROJECT_ROOT, "data", "processed", "livelihood_data.csv")
    process_dataset_b(INPUT_FILE, READINESS_OUT, LIVELIHOOD_OUT)
