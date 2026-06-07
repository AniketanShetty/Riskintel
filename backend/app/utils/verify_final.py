import os
import pandas as pd
import json

def run_verification():
    print("=== Missing values before cleaning ===")
    df_raw_a = pd.read_csv('../data/raw/loan_approval_dataset.csv')
    df_raw_b = pd.read_csv('../data/raw/RuralCreditData.csv')
    df_raw_c = pd.read_csv('../data/raw/External_Cibil_Dataset.csv')

    print(f"Dataset A (loan_approval_dataset.csv): {df_raw_a.isna().sum().sum()}")
    print(f"Dataset B (RuralCreditData.csv): {df_raw_b.isna().sum().sum()}")
    print(f"Dataset C (External_Cibil_Dataset.csv): {df_raw_c.isna().sum().sum()}")

    print("\n=== Missing values after cleaning ===")
    df_a = pd.read_csv('../data/processed/eligibility_data.csv')
    df_br = pd.read_csv('../data/processed/readiness_data.csv')
    df_bl = pd.read_csv('../data/processed/livelihood_data.csv')

    print(f"eligibility_data.csv: {df_a.isna().sum().sum()}")
    print(f"readiness_data.csv: {df_br.isna().sum().sum()}")
    print(f"livelihood_data.csv: {df_bl.isna().sum().sum()}")

    print("\n=== Output file names & shapes ===")
    print(f"eligibility_data.csv: {df_a.shape}")
    print(f"readiness_data.csv: {df_br.shape}")
    print(f"livelihood_data.csv: {df_bl.shape}")

    print("\n=== First 5 rows ===")
    print("eligibility_data.csv:")
    print(json.dumps(df_a.head(5).to_dict(orient='records'), indent=2))
    print("\nreadiness_data.csv:")
    print(json.dumps(df_br.head(5).to_dict(orient='records'), indent=2))
    print("\nlivelihood_data.csv:")
    print(json.dumps(df_bl.head(5).to_dict(orient='records'), indent=2))

    with open('../data/processed/risk_tier_thresholds.json') as f:
        print("\nrisk_tier_thresholds.json:")
        print(json.dumps(json.load(f), indent=2))

if __name__ == "__main__":
    run_verification()
